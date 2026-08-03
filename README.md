# DealerMind AI

Scalable decision-intelligence platform for automotive dealers operating across multiple markets.

## Product direction

DealerMind AI separates three questions:

- **Market Score:** Is the vehicle attractive for a selected sales market?
- **Dealer Score:** Is it attractive for this dealer's capabilities and economics?
- **Opportunity Score:** Is this specific offer worth acting on now?

The system preserves the facts, assumptions, factor contributions and configuration version behind every recommendation.

## Current foundation

- Multi-market data model, Poland first and Ukraine-ready
- Vehicle and marketplace-offer separation
- Price-history tracking
- Explainable configurable scoring primitives
- FastAPI REST API
- PostgreSQL and Alembic
- Docker Compose local environment
- Automated tests and GitHub Actions CI

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Open:

- API documentation: http://localhost:8000/docs
- Health endpoint: http://localhost:8000/health

Run tests:

```bash
docker compose run --rm api pytest
```

## Project doctrine

Start with [docs/DEVELOPER_BIBLE.md](docs/DEVELOPER_BIBLE.md).

Architecture decisions are stored in [docs/adr](docs/adr), and the prioritized work is in [docs/product/BACKLOG.md](docs/product/BACKLOG.md).
