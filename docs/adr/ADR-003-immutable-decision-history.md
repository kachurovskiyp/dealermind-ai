# ADR-003: Preserve immutable decision history

- Status: Accepted
- Date: 2026-08-03

## Decision

Scores and recommendations are snapshots. They store input data, factor contributions, configuration version and timestamp. Recalculation creates a new snapshot instead of updating the old one.

## Rationale

This permits auditing, comparison of forecast to outcome, rule calibration and honest evaluation of model quality.
