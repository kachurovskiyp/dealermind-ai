# Ubiquitous Language

This vocabulary is part of the domain contract. API, code, database and product language use the same terms.

| Term | Meaning |
|---|---|
| Market | Country-specific commercial context, initially Poland (`PL`) or Ukraine (`UA`), with its own currency, rules and demand. |
| Marketplace | A source of offers operating in a market, such as Otomoto or OLX. |
| Vehicle | The physical transport asset; VIN is its strongest identity. Never use `Car` as a domain entity. |
| Offer | A marketplace representation of a vehicle. It can change or disappear without changing the vehicle. |
| Price Observation | An immutable price seen for an offer at a specific time. |
| Opportunity | A potential profit-making decision linking a source offer to a target market. It is the acquisition aggregate root. |
| Market Score | Market attractiveness independent of a particular dealer. |
| Dealer Score | Fit for this dealer's costs, capabilities, preparation time and capital. |
| Opportunity Score | Overall prioritisation signal derived from the available evidence. |
| Score Snapshot | Immutable, versioned and explainable result containing factor contributions and missing factors. |
| Opportunity Decision | Immutable accept/reject/evaluate/reopen record. A correction is another decision, never an edit. |
| Acquisition | Execution of an accepted opportunity: inspection, negotiation and purchase. |
| Inventory Item | A vehicle owned or controlled by the business in a particular market. |
| Preparation | A concrete cosmetic, mechanical, electrical, body or documentation job before sale. |
| Sale | Completed transfer of an inventory item to a buyer in a market. |
| Vehicle Event | Immutable fact in a vehicle's lifecycle, recorded as an event with contextual payload. |

## Invariants

- A vehicle and its offers are separate identities.
- Every opportunity has one source offer and one target market.
- Scores are 0–100, explainable and tied to a configuration version.
- Price observations, score snapshots, opportunity decisions and vehicle events are append-only.
- Poland and Ukraine share the domain model; market-specific rules belong to configuration or market services.
- Historical facts are never overwritten. Later facts supersede them while preserving the decision trail.
