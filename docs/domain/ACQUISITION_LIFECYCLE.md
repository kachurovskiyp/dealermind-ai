# Acquisition lifecycle

The acquisition boundary turns an accepted decision into owned inventory without losing the
evidence trail.

```mermaid
sequenceDiagram
  participant O as Opportunity
  participant A as Acquisition
  participant I as InventoryItem
  participant E as VehicleEvent stream

  O->>A: Start from accepted opportunity
  A->>E: Append acquisition.started
  A->>I: Complete purchase
  A->>O: Mark opportunity acquired
  A->>E: Append purchase.completed
```

## Invariants

- Only an accepted opportunity can start an acquisition.
- An opportunity can create at most one acquisition.
- A completed or cancelled acquisition cannot be completed.
- Completing an acquisition creates exactly one inventory item in the opportunity target market.
- `acquisition.started` and `purchase.completed` are appended to vehicle history in the same
  database transaction as their state changes.
- Event payloads contain identifiers, price, currency and owning market needed for later audit.
