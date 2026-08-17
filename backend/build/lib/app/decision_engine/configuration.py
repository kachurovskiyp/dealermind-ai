"""Load and validate versioned scoring configuration."""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from app.decision_engine.scoring import ScoreType, ScoringConfigurationError


@dataclass(frozen=True, slots=True)
class ScoringDefinition:
    version: str
    weights: dict[ScoreType, dict[str, float]]


@lru_cache
def load_scoring_definition() -> ScoringDefinition:
    path = Path(__file__).parents[1] / "core" / "configuration" / "scoring.v1.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data.get("status") != "active":
        raise ScoringConfigurationError("scoring configuration must be active")
    version = str(data.get("version", "")).strip()
    if not version:
        raise ScoringConfigurationError("scoring configuration version is required")
    scores = data.get("scores")
    if not isinstance(scores, dict):
        raise ScoringConfigurationError("scores configuration is required")
    weights: dict[ScoreType, dict[str, float]] = {}
    for score_type in ScoreType:
        raw = scores.get(score_type.value)
        if not isinstance(raw, dict) or not raw:
            raise ScoringConfigurationError(f"weights for '{score_type.value}' are required")
        weights[score_type] = {str(key): float(value) for key, value in raw.items()}
    return ScoringDefinition(version=version, weights=weights)
