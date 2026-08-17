import asyncio
import logging
from datetime import timedelta
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.market_intelligence import StructuredListingProvider
from app.models.automation import ImportRun, ImportRunStatus, ImportSource
from app.models.domain import utcnow
from app.schemas.automation import ImportSourceCreate, ImportSourceUpdate
from app.schemas.imports import ListingImportBatch
from app.services.imports import import_listings

logger = logging.getLogger(__name__)


def list_sources(db: Session) -> list[ImportSource]:
    return list(db.scalars(select(ImportSource).order_by(ImportSource.name)))


def create_source(db: Session, payload: ImportSourceCreate) -> ImportSource:
    source = ImportSource(
        name=payload.name,
        provider_type="json_http",
        endpoint_url=str(payload.endpoint_url),
        interval_minutes=payload.interval_minutes,
        enabled=payload.enabled,
        next_run_at=utcnow() if payload.enabled else None,
        configuration=payload.configuration,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def update_source(
    db: Session, source_id: UUID, payload: ImportSourceUpdate
) -> ImportSource:
    source = db.get(ImportSource, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    changes = payload.model_dump(exclude_none=True)
    if "endpoint_url" in changes:
        changes["endpoint_url"] = str(changes["endpoint_url"])
    for field_name, value in changes.items():
        setattr(source, field_name, value)
    if payload.enabled is False:
        source.next_run_at = None
    elif source.enabled:
        source.next_run_at = utcnow() + timedelta(minutes=source.interval_minutes)
    db.commit()
    db.refresh(source)
    return source


def list_runs(db: Session, source_id: UUID | None = None) -> list[ImportRun]:
    statement = select(ImportRun)
    if source_id is not None:
        statement = statement.where(ImportRun.source_id == source_id)
    return list(db.scalars(statement.order_by(ImportRun.started_at.desc()).limit(100)))


def due_source_ids(db: Session) -> list[UUID]:
    now = utcnow()
    return list(
        db.scalars(
            select(ImportSource.id).where(
                ImportSource.enabled.is_(True),
                or_(ImportSource.next_run_at.is_(None), ImportSource.next_run_at <= now),
            )
        )
    )


def _batch_from_response(source: ImportSource, data: object) -> ListingImportBatch:
    if isinstance(data, list):
        payload = {"provider": source.name, "records": data}
    elif isinstance(data, dict):
        payload = {**data, "provider": source.name}
    else:
        raise ValueError("source response must be a JSON array or object")
    return ListingImportBatch.model_validate(payload)


async def execute_source(source_id: UUID, trigger: str) -> ImportRun:
    db = SessionLocal()
    try:
        source = db.get(ImportSource, source_id)
        if source is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
        run = ImportRun(source_id=source.id, trigger=trigger)
        source.next_run_at = utcnow() + timedelta(minutes=source.interval_minutes)
        db.add(run)
        db.commit()
        db.refresh(run)
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
                response = await client.get(source.endpoint_url)
                response.raise_for_status()
                batch = _batch_from_response(source, response.json())
            result = import_listings(
                db,
                StructuredListingProvider(batch.records, name=source.name),
            )
            run.received = result.received
            run.created = result.created
            run.updated = result.updated
            run.unchanged = result.unchanged
            run.error_count = len(result.errors)
            run.error_message = "; ".join(error.message for error in result.errors) or None
            run.status = (
                ImportRunStatus.PARTIAL if result.errors else ImportRunStatus.COMPLETED
            )
        except Exception as exc:
            db.rollback()
            run = db.get(ImportRun, run.id)
            if run is None:
                raise
            run.status = ImportRunStatus.FAILED
            run.error_count = 1
            run.error_message = str(exc)[:4000]
        now = utcnow()
        source = db.get(ImportSource, source_id)
        if source is not None:
            source.last_run_at = now
            source.next_run_at = (
                now + timedelta(minutes=source.interval_minutes) if source.enabled else None
            )
        run.completed_at = now
        db.commit()
        db.refresh(run)
        return run
    finally:
        db.close()


async def scheduler_loop(stop: asyncio.Event) -> None:
    try:
        await asyncio.wait_for(stop.wait(), timeout=5)
    except TimeoutError:
        pass
    while not stop.is_set():
        try:
            with SessionLocal() as db:
                source_ids = due_source_ids(db)
            for source_id in source_ids:
                if stop.is_set():
                    break
                await execute_source(source_id, trigger="schedule")
        except Exception:
            logger.exception("scheduled import cycle failed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=30)
        except TimeoutError:
            pass
