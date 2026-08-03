"""Deterministic and explainable weighted scoring primitives."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from typing import Mapping


class ScoreType(StrEnum):
    MARKET = "market"
    DEALER = "dealer"
    OPPORTUNITY = "opportunity"


@dataclass(frozen=True, slots=True)
class FactorContribution:
    key: str
    value: float
    weight: float
    weighted_points: float
    explanation: str | None = None


@dataclass(frozen=True, slots=True)
class ScoreResult:
    score_type: ScoreType
    value: float
    configuration_version: str
    contributions: tuple[FactorContribution, ...]
    missing_factors: tuple[str, ...]


class ScoringConfigurationError(ValueError):
    """Raised when a scoring definition cannot produce a valid score."""


def calculate_weighted_score(
    *,
    score_type: ScoreType,
    factor_values: Mapping[str, float],
    factor_weights: Mapping[str, float],
    configuration_version: str,
    explanations: Mapping[str, str] | None = None,
) -> ScoreResult:
    """Calculate a 0–100 score and retain each factor's contribution.

    Factor values must already be normalized to the 0–100 range. Missing
    factors are excluded and remaining positive weights are re-normalized.
    This behavior is explicit in the result so recommendation code can lower
    confidence when important data is absent.
    """

    if not configuration_version.strip():
        raise ScoringConfigurationError("configuration_version is required")
    if not factor_weights:
        raise ScoringConfigurationError("at least one factor weight is required")

    invalid_weights = {
        key: weight
        for key, weight in factor_weights.items()
        if not isfinite(weight) or weight < 0
    }
    if invalid_weights:
        raise ScoringConfigurationError(f"invalid factor weights: {invalid_weights}")

    available: list[tuple[str, float, float]] = []
    missing: list[str] = []
    for key, weight in factor_weights.items():
        if weight == 0:
            continue
        value = factor_values.get(key)
        if value is None:
            missing.append(key)
            continue
        if not isfinite(value) or not 0 <= value <= 100:
            raise ScoringConfigurationError(
                f"factor '{key}' must be a finite value between 0 and 100"
            )
        available.append((key, value, weight))

    total_weight = sum(weight for _, _, weight in available)
    if total_weight <= 0:
        raise ScoringConfigurationError("no positively weighted factors are available")

    details: list[FactorContribution] = []
    score = 0.0
    for key, value, raw_weight in available:
        normalized_weight = raw_weight / total_weight
        points = value * normalized_weight
        score += points
        details.append(
            FactorContribution(
                key=key,
                value=round(value, 4),
                weight=round(normalized_weight, 6),
                weighted_points=round(points, 4),
                explanation=(explanations or {}).get(key),
            )
        )

    return ScoreResult(
        score_type=score_type,
        value=round(score, 2),
        configuration_version=configuration_version,
        contributions=tuple(details),
        missing_factors=tuple(sorted(missing)),
    )
