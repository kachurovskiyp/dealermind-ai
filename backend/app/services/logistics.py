"""Explainable Logistics Cost v1 with cached geocoding and append-only results."""

from decimal import Decimal, ROUND_HALF_UP
from math import asin, cos, radians, sin, sqrt
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.domain import LogisticsProfile, LogisticsSnapshot, Offer, Opportunity
from app.schemas.logistics import LogisticsProfileUpsert
from app.services.ranking import rank_opportunity

CONFIGURATION_VERSION = "logistics-v1"
ROAD_DISTANCE_FACTOR = Decimal("1.20")


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def haversine_km(lat1: Decimal, lon1: Decimal, lat2: Decimal, lon2: Decimal) -> Decimal:
    """Great-circle distance between two WGS84 points."""
    phi1, phi2 = radians(float(lat1)), radians(float(lat2))
    delta_phi = radians(float(lat2 - lat1))
    delta_lambda = radians(float(lon2 - lon1))
    value = sin(delta_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
    return Decimal(str(6371.0088 * 2 * asin(sqrt(value))))


def calculate_costs(
    direct_distance_km: Decimal,
    fixed_cost: Decimal,
    cost_per_km: Decimal,
    trip_multiplier: Decimal,
    cross_border_surcharge: Decimal,
    cross_border: bool,
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    travelled_km = (direct_distance_km * ROAD_DISTANCE_FACTOR * trip_multiplier).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )
    distance_cost = _money(travelled_km * cost_per_km)
    border_cost = _money(cross_border_surcharge if cross_border else Decimal(0))
    total = _money(fixed_cost + distance_cost + border_cost)
    return travelled_km, distance_cost, border_cost, total


async def geocode(label: str, country_code: str) -> tuple[Decimal, Decimal, str]:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            response = await client.get(
                settings.geocoding_url,
                params={
                    "q": label,
                    "countrycodes": country_code.lower(),
                    "format": "jsonv2",
                    "limit": 1,
                },
                headers={"User-Agent": settings.geocoding_user_agent},
            )
            response.raise_for_status()
            results = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Не удалось определить координаты. "
                "Повторите попытку позже."
            ),
        ) from exc
    if not isinstance(results, list) or not results:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Не удалось найти на карте: {label}",
        )
    result = results[0]
    return Decimal(str(result["lat"])), Decimal(str(result["lon"])), str(result["display_name"])


def get_profile(db: Session) -> LogisticsProfile | None:
    return db.scalar(select(LogisticsProfile).order_by(LogisticsProfile.created_at).limit(1))


async def upsert_profile(db: Session, payload: LogisticsProfileUpsert) -> LogisticsProfile:
    latitude, longitude, resolved_label = await geocode(
        payload.origin_label, payload.origin_country_code
    )
    profile = get_profile(db)
    values = payload.model_dump()
    values.update(
        origin_label=resolved_label,
        origin_latitude=latitude,
        origin_longitude=longitude,
    )
    if profile is None:
        profile = LogisticsProfile(**values)
        db.add(profile)
    else:
        for key, value in values.items():
            setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


async def calculate_logistics(db: Session, opportunity_id: UUID) -> LogisticsSnapshot:
    opportunity = db.scalar(
        select(Opportunity)
        .where(Opportunity.id == opportunity_id)
        .options(
            selectinload(Opportunity.offer),
            selectinload(Opportunity.logistics_snapshots),
        )
    )
    if opportunity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Возможность не найдена"
        )
    profile = get_profile(db)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Сначала настройте профиль логистики",
        )
    if profile.currency != opportunity.currency:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Валюта профиля логистики не совпадает "
                "с валютой возможности"
            ),
        )
    offer = opportunity.offer
    region = offer.raw_data.get("location_region")
    country = str(offer.raw_data.get("country_code") or "").upper()
    destination = ", ".join(str(value) for value in (offer.location, region) if value)
    if not destination or len(country) != 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Для расчёта нужны населённый пункт "
                "и страна автомобиля"
            ),
        )
    cached = offer.raw_data.get("geocoding")
    if isinstance(cached, dict) and cached.get("query") == destination:
        latitude = Decimal(str(cached["latitude"]))
        longitude = Decimal(str(cached["longitude"]))
        resolved_destination = str(cached.get("display_name") or destination)
    else:
        latitude, longitude, resolved_destination = await geocode(destination, country)
        offer.raw_data = {
            **offer.raw_data,
            "geocoding": {
                "query": destination,
                "latitude": str(latitude),
                "longitude": str(longitude),
                "display_name": resolved_destination,
                "provider": "OpenStreetMap Nominatim",
            },
        }
    direct_km = haversine_km(
        profile.origin_latitude, profile.origin_longitude, latitude, longitude
    )
    cross_border = profile.origin_country_code != country
    distance_km, distance_cost, border_cost, total = calculate_costs(
        direct_km,
        profile.fixed_cost,
        profile.cost_per_km,
        profile.trip_multiplier,
        profile.cross_border_surcharge,
        cross_border,
    )
    previous = opportunity.logistics_snapshots[-1] if opportunity.logistics_snapshots else None
    base_costs = max(
        Decimal(0),
        (opportunity.expected_costs or Decimal(0))
        - (previous.total_cost if previous else 0),
    )
    snapshot = LogisticsSnapshot(
        opportunity_id=opportunity.id,
        profile_id=profile.id,
        origin_label=profile.origin_label,
        destination_label=resolved_destination,
        origin_latitude=profile.origin_latitude,
        origin_longitude=profile.origin_longitude,
        destination_latitude=latitude,
        destination_longitude=longitude,
        distance_km=distance_km,
        fixed_cost=profile.fixed_cost,
        distance_cost=distance_cost,
        cross_border_cost=border_cost,
        total_cost=total,
        currency=profile.currency,
        configuration_version=CONFIGURATION_VERSION,
        explanation={
            "method": "haversine_with_road_factor",
            "direct_distance_km": round(float(direct_km), 1),
            "road_distance_factor": float(ROAD_DISTANCE_FACTOR),
            "trip_multiplier": float(profile.trip_multiplier),
            "cost_per_km": str(profile.cost_per_km),
            "cross_border": cross_border,
            "base_costs_preserved": str(base_costs),
            "geocoding_provider": "OpenStreetMap Nominatim",
        },
    )
    db.add(snapshot)
    opportunity.expected_costs = _money(base_costs + total)
    if (
        opportunity.expected_sale_price is not None
        and opportunity.expected_purchase_price is not None
    ):
        opportunity.expected_profit = _money(
            opportunity.expected_sale_price
            - opportunity.expected_purchase_price
            - opportunity.expected_costs
        )
    rank_opportunity(db, opportunity)
    db.commit()
    db.refresh(snapshot)
    return snapshot
