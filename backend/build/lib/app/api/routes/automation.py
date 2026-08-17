from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.automation import (
    ImportRunRead,
    ImportSourceCreate,
    ImportSourceRead,
    ImportSourceUpdate,
)
from app.services.automation import (
    create_source,
    execute_source,
    list_runs,
    list_sources,
    update_source,
)

router = APIRouter(prefix="/automation", tags=["automation"])


@router.get("/sources", response_model=list[ImportSourceRead])
def get_sources(db: Session = Depends(get_db)) -> list[ImportSourceRead]:
    return list_sources(db)


@router.post("/sources", response_model=ImportSourceRead)
def post_source(
    payload: ImportSourceCreate, db: Session = Depends(get_db)
) -> ImportSourceRead:
    return create_source(db, payload)


@router.patch("/sources/{source_id}", response_model=ImportSourceRead)
def patch_source(
    source_id: UUID,
    payload: ImportSourceUpdate,
    db: Session = Depends(get_db),
) -> ImportSourceRead:
    return update_source(db, source_id, payload)


@router.post("/sources/{source_id}/run", response_model=ImportRunRead)
async def post_source_run(source_id: UUID) -> ImportRunRead:
    return await execute_source(source_id, trigger="manual")


@router.get("/runs", response_model=list[ImportRunRead])
def get_runs(
    source_id: UUID | None = None, db: Session = Depends(get_db)
) -> list[ImportRunRead]:
    return list_runs(db, source_id)
