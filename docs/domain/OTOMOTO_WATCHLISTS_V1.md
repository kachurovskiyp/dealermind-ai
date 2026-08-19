# Otomoto Watchlists v1

An **Otomoto Watchlist** is a user-configured search URL that DealerMind checks on a
bounded schedule. It is implemented as an `ImportSource` with provider type
`otomoto_search`, so every execution is recorded in the existing append-only
`ImportRun` history.

## Flow

1. The owner configures filters on Otomoto and saves the resulting public search URL.
2. DealerMind discovers at most 25 public listing links per run (10 by default).
3. Listing pages are fetched sequentially with a delay and strict redirect, size, and
   public-network checks.
4. Complete previews enter the existing Market Intelligence import pipeline.
5. Existing offers are updated, price observations are appended, and new opportunities
   are ranked by the current versioned scoring configuration.

The adapter does not bypass authentication, CAPTCHAs, rate limits, or access controls.
The minimum automatic interval is 30 minutes. A failed or partially parsed run remains
visible in `ImportRun` history with its error explanation.

## Limits of v1

- Poland and the existing `otomoto` marketplace only.
- First search-results page only.
- No proxy rotation or anti-bot circumvention.
- Missing required listing fields cause that listing to be skipped and explained.

