# Market Intelligence v1

Market Intelligence ingests provider-neutral listing records and sends them through the existing
domain and ranking pipeline.

```text
Provider file → validation → market/marketplace resolution → deduplication
→ Vehicle + Offer → PriceObservation → Opportunity → Ranking v1
```

## Provider boundary

`ListingProvider` exposes normalized `ListingImportRecord` values. CSV and structured JSON are the
first adapters. A future official marketplace API or permitted collector implements the same
boundary without changing the domain service.

## Identity and deduplication

- Offer identity is `(marketplace_id, external_id)`.
- A repeated identity updates the existing offer.
- A new price appends `PriceObservation`; it never edits price history.
- VIN reuses an existing `Vehicle` when it is available.
- Repeated records without changed price or listing data are reported as unchanged.
- A new offer creates one Opportunity for the requested target market and ranks it immediately.

## Required import columns

`market_code`, `marketplace_slug`, `target_market_code`, `external_id`, `url`, `title`, `make`,
`model`, `price`, `currency`.

Expected sale price and costs are optional but materially improve Dealer Score and Opportunity
Score. Records are processed inside database savepoints: one invalid record is reported without
discarding valid records in the same batch.
