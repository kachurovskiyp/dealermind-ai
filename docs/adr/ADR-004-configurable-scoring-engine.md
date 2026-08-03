# ADR-004: Use a configurable scoring engine

- Status: Accepted
- Date: 2026-08-03

## Decision

Scoring weights, thresholds and enabled factors are loaded from versioned configuration. The engine validates that weights are non-negative and normalizes them at runtime.

No production score formula may contain unexplained business weights embedded directly in application code.
