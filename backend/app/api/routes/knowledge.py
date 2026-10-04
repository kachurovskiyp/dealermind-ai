from fastapi import APIRouter, HTTPException, status

from app.schemas.knowledge import (
    DealerAssessmentRead,
    KnowledgeProfileRead,
    KnowledgeProfileSummaryRead,
)
from app.services.dealer_knowledge import assess_dealer_configuration
from app.services.knowledge import find_knowledge_profile, knowledge_profiles

router = APIRouter(prefix="/knowledge", tags=["vehicle knowledge"])


@router.get("/dealer-assessment", response_model=DealerAssessmentRead)
def dealer_assessment(
    make: str,
    model: str,
    generation: str | None = None,
    engine: str | None = None,
    gearbox: str | None = None,
    power_hp: int | None = None,
) -> DealerAssessmentRead:
    return DealerAssessmentRead.model_validate(
        assess_dealer_configuration(
            make=make,
            model=model,
            generation=generation,
            engine=engine,
            gearbox=gearbox,
            power_hp=power_hp,
        )
    )


@router.get("/profiles", response_model=list[KnowledgeProfileSummaryRead])
def profiles() -> list[KnowledgeProfileSummaryRead]:
    return [KnowledgeProfileSummaryRead.model_validate(item) for item in knowledge_profiles()]


@router.get("/profiles/{slug}", response_model=KnowledgeProfileRead)
def profile(slug: str) -> KnowledgeProfileRead:
    item = find_knowledge_profile(slug)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge profile not found")
    return KnowledgeProfileRead.model_validate(item)
