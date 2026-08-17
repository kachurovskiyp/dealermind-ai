# ADR-005: Local import scheduler for Automation v1

## Status

Accepted for the single-instance product stage.

## Decision

DealerMind runs a lightweight scheduler inside the API process. Every 30 seconds it finds enabled
sources whose `next_run_at` is due, fetches their JSON feed and sends normalized records through
the existing Market Intelligence pipeline.

Source configuration and run history live in PostgreSQL. A source is leased by moving
`next_run_at` before network access. Failures are recorded and scheduled for the next interval;
they never stop other sources or the API.

## Consequences

- The local Docker installation needs no separate worker or queue.
- Manual and scheduled executions use the same code path.
- Only trusted JSON endpoints should be configured in this version.
- Before running multiple API replicas, scheduling must move to a dedicated worker or use a
  distributed PostgreSQL lock. The in-process scheduler is intentionally not a multi-node design.
