# Domain model v0.1

## Bounded contexts

### Market Intelligence
`Market`, `Marketplace`, `Offer`, `PriceObservation`, `MarketComparable`, `DemandMetric`

### Acquisition
`Opportunity`, `Inspection`, `Negotiation`, `AcquisitionDecision`, `Purchase`

### Inventory
`Vehicle`, `InventoryItem`, `VehicleEvent`, `Document`, `MediaAsset`

### Preparation
`PreparationPlan`, `PreparationJob`, `WorkProvider`, `WorkCapability`, `PartUsage`, `PreparationBlocker`

### Sales
`SalesListing`, `Lead`, `Viewing`, `Reservation`, `Sale`

### Finance
`Expense`, `Revenue`, `CapitalAllocation`, `ProfitSnapshot`, `ExchangeRateSnapshot`

### Decision Intelligence
`ScoreDefinition`, `ScoreFactor`, `ScoreSnapshot`, `Recommendation`, `DecisionOutcome`

## Critical relationships

- A `Vehicle` is the physical identity of a car.
- An `Offer` is a marketplace representation and may exist before vehicle identity is confirmed.
- An `Opportunity` links an offer to an intended acquisition and target sales market.
- An `InventoryItem` starts when the business acquires or accepts responsibility for a vehicle.
- A `PreparationPlan` contains one or more `PreparationJob` records.
- A `ScoreSnapshot` is immutable and references the data available at calculation time.

## Lifecycle events

`offer.discovered` → `opportunity.created` → `inspection.completed` → `purchase.completed` → `vehicle.arrived` → `preparation.started` → `preparation.completed` → `sales_listing.published` → `sale.completed` → `deal.closed`
