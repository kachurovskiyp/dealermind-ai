import pytest

from app.decision_engine import (
    ScoreType,
    ScoringConfigurationError,
    calculate_weighted_score,
)


def test_weighted_score_is_explainable() -> None:
    result = calculate_weighted_score(
        score_type=ScoreType.DEALER,
        factor_values={"roi": 80, "preparation_duration": 60},
        factor_weights={"roi": 3, "preparation_duration": 1},
        configuration_version="test-v1",
        explanations={"roi": "Expected return on invested capital"},
    )

    assert result.value == 75.0
    assert result.configuration_version == "test-v1"
    assert result.contributions[0].weight == 0.75
    assert result.contributions[0].explanation is not None


def test_missing_factors_are_reported_and_available_weights_are_normalized() -> None:
    result = calculate_weighted_score(
        score_type=ScoreType.MARKET,
        factor_values={"liquidity": 90},
        factor_weights={"liquidity": 1, "demand": 1},
        configuration_version="test-v1",
    )

    assert result.value == 90.0
    assert result.missing_factors == ("demand",)


def test_invalid_factor_value_is_rejected() -> None:
    with pytest.raises(ScoringConfigurationError):
        calculate_weighted_score(
            score_type=ScoreType.OPPORTUNITY,
            factor_values={"freshness": 101},
            factor_weights={"freshness": 1},
            configuration_version="test-v1",
        )
