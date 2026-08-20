# Poland Market Analytics v2

The active product scope is the domestic Polish vehicle market. Every metric in
this dashboard is filtered to market code `PL` and currency `PLN`. Multi-market
support remains an architectural capability, but it is not mixed into these results.

## Ubiquitous Language

- **Market Segment** — listings matching the active vehicle, seller and region filters.
- **Price Position** — the price percentile of a listing among the same make and model,
  allowing a two-year difference in production year.
- **Days Observed** — elapsed time since DealerMind first saw the listing. It is not yet
  presented as confirmed time-to-sale.
- **Price Reduction** — a later PLN price observation lower than the preceding one.
- **Seller Mix** — distribution between private, dealer and unknown sellers.

## Data quality rules

- Unknown seller and region values are reported explicitly and never guessed.
- Median prices use the latest PLN observation for each imported offer.
- Price history is derived from append-only `PriceObservation` records.
- Liquidity is deliberately deferred until listing disappearance history is reliable.
