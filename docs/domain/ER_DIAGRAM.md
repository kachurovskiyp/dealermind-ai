# Domain Core ER diagram

```mermaid
erDiagram
  MARKET ||--o{ MARKETPLACE : contains
  MARKETPLACE ||--o{ OFFER : publishes
  VEHICLE ||--o{ OFFER : represented_by
  OFFER ||--o{ PRICE_OBSERVATION : has
  OFFER ||--o{ OPPORTUNITY : creates
  MARKET ||--o{ OPPORTUNITY : target_for
  OPPORTUNITY ||--o{ SCORE_SNAPSHOT : evaluated_by
  OPPORTUNITY ||--o{ OPPORTUNITY_DECISION : decided_through
  OPPORTUNITY ||--o| ACQUISITION : progresses_to
  ACQUISITION ||--o| INVENTORY_ITEM : creates
  VEHICLE ||--o{ INVENTORY_ITEM : stocked_as
  MARKET ||--o{ INVENTORY_ITEM : owns
  INVENTORY_ITEM ||--o{ PREPARATION : requires
  INVENTORY_ITEM ||--o| SALE : completes_as
  MARKET ||--o{ SALE : occurs_in
  VEHICLE ||--o{ VEHICLE_EVENT : records
```

The four history streams (`PRICE_OBSERVATION`, `SCORE_SNAPSHOT`, `OPPORTUNITY_DECISION`, `VEHICLE_EVENT`) are append-only. This is event-driven state history, not full event sourcing: current aggregate state remains queryable in its own table.
