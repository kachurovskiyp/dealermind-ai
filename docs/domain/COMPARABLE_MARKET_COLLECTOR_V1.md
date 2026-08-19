# Comparable Market Collector v1

The Comparable Market is evidence for valuation, not an opportunity pipeline. Collected
listings therefore never create `Offer` or `Opportunity` records and never appear in the
Opportunity Feed.

Each user-triggered collection creates a `ComparableCollection` audit record and up to 25
immutable `ComparableListing` observations. For Watchlist-originated opportunities the
original filtered Otomoto search URL is reused. Manual opportunities use a generated
make/model search URL.

After collection, Market Valuation deduplicates observations by external listing ID, applies
the versioned year and mileage eligibility rules, appends a new `ValuationSnapshot`, updates
automatically managed expected sale price and costs, and recalculates all scores. Manual
dealer-entered financial assumptions remain authoritative.

The collector uses the same bounded network and rate controls as Otomoto Watchlists and does
not bypass authentication, CAPTCHAs, rate limits, or access controls.
