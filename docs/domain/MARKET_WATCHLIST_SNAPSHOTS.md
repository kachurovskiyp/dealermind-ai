# Market Watchlist Snapshots

Every successful Polish Otomoto watchlist run creates an append-only
`MarketSegmentSnapshot`. Existing `ImportSource` records with provider type
`otomoto_search` are therefore the product's Market Watchlists; no duplicate
configuration is required.

## Snapshot contents

- listing count returned by the run;
- new and updated offers;
- median, minimum and maximum PLN price;
- latest price reductions;
- private, dealer and unknown seller counts;
- observed makes, models, years and regions;
- source URL, run ID and configuration version.

The `market-snapshot-v1` method uses the latest PLN price for every offer returned
by that import run. Re-running a watchlist appends a new snapshot and never edits
the earlier result. The market dashboard groups these records by watchlist, uses
the latest snapshot from each Warsaw calendar day and shows the latest 30 days.

These observations describe the search sample, not the whole Polish market. A
future Liquidity Score may use the series only after disappearance tracking and
enough elapsed time make the signal reliable.
