from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.automation import PolandFleetSnapshot
from app.schemas.fleet import FleetCollectionStatusRead, FleetProfileRead, FleetSnapshotRead, FleetStatusRead
from app.services.fleet_intelligence import begin_collection, collection_status, latest_snapshot, list_snapshots, monitored_profiles, collect_in_background

router = APIRouter(prefix="/fleet-intelligence", tags=["Poland fleet intelligence"])

@router.get("/status", response_model=FleetStatusRead)
def fleet_status() -> FleetStatusRead:
    return FleetStatusRead(configured=True, message="Производственный CEPiK API готов к сбору")

@router.get("/profiles", response_model=list[FleetProfileRead])
def profiles(db: Session = Depends(get_db)) -> list[FleetProfileRead]:
    return [FleetProfileRead(slug=str(p["slug"]), make=str(p["make"]), model=str(p["model"]), generation=str(p.get("generation", "")), latest=latest_snapshot(db, str(p["slug"]))) for p in monitored_profiles()]

@router.get("/profiles/{profile_slug}/snapshots", response_model=list[FleetSnapshotRead])
def snapshots(profile_slug: str, db: Session = Depends(get_db)) -> list[PolandFleetSnapshot]:
    return list_snapshots(db, profile_slug)

@router.get("/profiles/{profile_slug}/latest", response_model=FleetSnapshotRead | None)
def latest(profile_slug: str, db: Session = Depends(get_db)) -> PolandFleetSnapshot | None:
    return latest_snapshot(db, profile_slug)


@router.get("/profiles/{profile_slug}/collection-status", response_model=FleetCollectionStatusRead)
def get_collection_status(profile_slug: str) -> FleetCollectionStatusRead:
    return FleetCollectionStatusRead(**collection_status(profile_slug))

@router.post("/profiles/{profile_slug}/collect", response_model=FleetCollectionStatusRead, status_code=status.HTTP_202_ACCEPTED)
def collect(profile_slug: str, background_tasks: BackgroundTasks, period_days: int = 30) -> FleetCollectionStatusRead:
    if not any(str(profile["slug"]) == profile_slug for profile in monitored_profiles()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fleet monitoring is not enabled for this knowledge profile")
    outcome = begin_collection(profile_slug)
    if outcome["state"] == "collecting" and outcome["message"].startswith("Собираем"):
        background_tasks.add_task(collect_in_background, profile_slug, max(1, min(period_days, 31)))
    return FleetCollectionStatusRead(**outcome)
