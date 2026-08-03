# Product backlog

## Milestone 1 — DealerMind Core

### DM-001 Foundation hardening
- Remove generated files from repository.
- Validate Docker startup and migrations.
- Add linting, type checking and test commands to CI.

### DM-002 Decision vocabulary
- Add score types and immutable score result contracts.
- Add configurable weighted scoring engine.
- Persist score definitions and snapshots in a later database slice.

### DM-003 Deal lifecycle model
- Model opportunity, purchase, inventory item and lifecycle events.
- Create a vehicle timeline endpoint.

### DM-004 Preparation intelligence
- Record preparation plan and individual jobs.
- Separate active work from waiting time.
- Separate internal, external and mixed execution.
- Calculate planned/actual preparation cost and duration.

### DM-005 Financial outcome
- Record acquisition, transport, preparation and selling costs.
- Calculate net profit, ROI, capital days and profit per capital-day.

## Milestone 2 — Market Intelligence Poland

### DM-101 Manual offer ingestion
- Accept normalized offer payload and raw source payload.
- Detect duplicate source offers.
- Append price observations.

### DM-102 First marketplace adapter
- Select source only after reviewing terms and available official access.
- Implement rate limits, retry policy and source health monitoring.

### DM-103 Comparable pricing
- Build transparent comparable-set selection.
- Calculate median, range and confidence.

## Milestone 3 — Cross-market analysis

- Poland and Ukraine target-market profiles.
- Currency and exchange-rate snapshots.
- Transport, import and compliance cost models.
- Cross-market opportunity comparison.
