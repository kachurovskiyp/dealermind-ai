from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

from app.models.domain import Opportunity, ScoreKind, ScoreSnapshot
from app.schemas.opportunity import ScoreCalculate
from app.services.opportunities import calculate_and_store_score


def test_scoring_result_is_persisted_with_explanation_and_version() -> None:
    db = MagicMock()
    db.get.return_value = Opportunity()
    db.refresh.side_effect = lambda snapshot: setattr(snapshot, "id", uuid4())
    opportunity_id = uuid4()

    snapshot = calculate_and_store_score(
        db,
        opportunity_id,
        ScoreCalculate(
            kind=ScoreKind.DEALER,
            factor_values={"roi": 80, "preparation_duration": 60},
            factor_weights={"roi": 3, "preparation_duration": 1},
            configuration_version="scoring-v1",
            explanations={"roi": "Expected return on invested capital"},
        ),
    )

    assert isinstance(snapshot, ScoreSnapshot)
    assert snapshot.value == Decimal("75.0")
    assert snapshot.configuration_version == "scoring-v1"
    assert snapshot.contributions[0]["weighted_points"] == 60.0
    assert snapshot.contributions[0]["explanation"] is not None
    db.add.assert_called_once_with(snapshot)
    db.commit.assert_called_once()
