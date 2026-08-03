# DealerMind AI

Scalable decision-support platform for automotive dealers operating across multiple markets.

## MVP scope

- Multi-market data model (Poland first, Ukraine-ready)
- Vehicle and marketplace offer storage
- Price-history tracking
- Rule-based opportunity scoring
- FastAPI REST API
- PostgreSQL + Alembic
- Docker Compose local environment
- Automated tests and GitHub Actions CI

## Quick start

1. Copy environment variables:

```bash
cp .env.example .env
```

2. Start services:

```bash
docker compose up --build
```

3. Open API documentation:

- http://localhost:8000/docs
- http://localhost:8000/health

4. Run tests:

```bash
docker compose run --rm api pytest
```

## Initial API

- `GET /health`
- `GET /api/v1/markets`
- `POST /api/v1/markets`
- `GET /api/v1/offers`
- `POST /api/v1/offers`

## Architecture principles

1. Markets are first-class entities.
2. A vehicle and an offer are separate concepts.
3. Raw source data is preserved for traceability.
4. AI explains recommendations; deterministic services calculate prices, costs, and scores.
5. Marketplace integrations are adapters, not core-domain dependencies.

See [docs/ROADMAP.md](docs/ROADMAP.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
