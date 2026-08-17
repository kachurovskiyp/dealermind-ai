from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.market_intelligence import CsvListingProvider, StructuredListingProvider
from app.schemas.imports import ListingImportBatch, ListingImportResult
from app.services.imports import import_listings

router = APIRouter(prefix="/imports", tags=["market intelligence"])


@router.post("/listings", response_model=ListingImportResult)
def post_listing_import(
    payload: ListingImportBatch, db: Session = Depends(get_db)
) -> ListingImportResult:
    return import_listings(db, StructuredListingProvider(payload.records, payload.provider))


@router.post("/listings/csv", response_model=ListingImportResult)
def post_csv_listing_import(
    content: str = Body(media_type="text/csv"),
    db: Session = Depends(get_db),
) -> ListingImportResult:
    try:
        return import_listings(db, CsvListingProvider(content))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
