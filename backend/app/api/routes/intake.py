from fastapi import APIRouter, HTTPException, status

from app.market_intelligence.link_intake import fetch_listing_preview
from app.schemas.intake import LinkPreviewRead, LinkPreviewRequest

router = APIRouter(prefix="/intake", tags=["market intelligence"])


@router.post("/link-preview", response_model=LinkPreviewRead)
async def post_link_preview(payload: LinkPreviewRequest) -> LinkPreviewRead:
    try:
        return await fetch_listing_preview(str(payload.url))
    except (ValueError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The listing page could not be fetched",
        ) from exc
