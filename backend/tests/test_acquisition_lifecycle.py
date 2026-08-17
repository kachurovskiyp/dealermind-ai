import pytest
from fastapi import HTTPException

from app.models.domain import (
    Acquisition,
    AcquisitionStatus,
    InventoryItem,
    Opportunity,
    OpportunityStatus,
)
from app.services.acquisitions import (
    ensure_acquisition_can_complete,
    ensure_acquisition_can_start,
)


def test_only_accepted_opportunity_can_start_acquisition() -> None:
    accepted = Opportunity(status=OpportunityStatus.ACCEPTED)
    ensure_acquisition_can_start(accepted)

    with pytest.raises(HTTPException) as error:
        ensure_acquisition_can_start(Opportunity(status=OpportunityStatus.EVALUATING))
    assert error.value.status_code == 409


def test_opportunity_cannot_have_two_acquisitions() -> None:
    opportunity = Opportunity(status=OpportunityStatus.ACCEPTED)
    opportunity.acquisition = Acquisition()

    with pytest.raises(HTTPException, match="already has"):
        ensure_acquisition_can_start(opportunity)


def test_active_acquisition_can_complete() -> None:
    ensure_acquisition_can_complete(Acquisition(status=AcquisitionStatus.NEGOTIATING))


def test_completed_acquisition_cannot_complete_twice() -> None:
    acquisition = Acquisition(status=AcquisitionStatus.COMPLETED)
    acquisition.inventory_item = InventoryItem()

    with pytest.raises(HTTPException) as error:
        ensure_acquisition_can_complete(acquisition)
    assert error.value.status_code == 409
