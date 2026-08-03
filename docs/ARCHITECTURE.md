# Architecture

## Core domains

- **Market**: country-level commercial context, currency, tax/import rules, buyer preferences.
- **Marketplace**: source of offers inside a market.
- **Vehicle**: normalized physical vehicle identity and specifications.
- **Offer**: a seller's listing for a vehicle at a point in time.
- **Price observation**: immutable price snapshot used for market history.
- **Opportunity**: future module comparing purchase, preparation, logistics, import, and sale scenarios.

## Layers

1. Collectors ingest raw offers.
2. Normalization converts source-specific fields into the domain model.
3. Analytics computes market statistics and comparable sets.
4. Decision engine scores acquisition and cross-market opportunities.
5. AI layer explains evidence and supports natural-language queries.
6. Interfaces deliver results through API, Telegram, and later a web dashboard.

## Non-negotiable rules

- Preserve raw source payloads.
- Never let an LLM be the authoritative calculator for money or taxes.
- Every recommendation must expose its evidence and assumptions.
- Separate Polish and Ukrainian market profiles while sharing the same core schema.
