# Roadmap v1

## Sprint 0 — Foundation

- Repository, Docker, PostgreSQL, FastAPI, Alembic, CI
- Market / Marketplace / Vehicle / Offer / PriceObservation entities
- Seed Poland and Ukraine markets

## Sprint 1 — Manual ingestion

- Endpoint to submit a marketplace URL or normalized offer
- Validation, deduplication, price-history updates
- Initial comparable-set query

## Sprint 2 — First marketplace adapter

- Select one source with a legally and technically acceptable ingestion method
- Scheduled collection
- Change detection and inactive-offer detection

## Sprint 3 — Polish market analytics

- Median and percentile pricing
- Days-on-market proxy
- Price-drop frequency
- Liquidity and data-quality scores

## Sprint 4 — Acquisition decision engine

- Purchase ceiling
- Preparation-cost scenarios
- Margin and ROI calculation
- Explainable opportunity score

## Sprint 5 — Ukraine market profile

- Ukrainian marketplaces and currency normalization
- Import/logistics/tax cost model as versioned rules
- Poland-to-Ukraine opportunity comparison

## Sprint 6 — Assistant interface

- Telegram notifications
- Natural-language questions over verified analytics
- Daily acquisition shortlist
