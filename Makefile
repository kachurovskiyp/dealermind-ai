.PHONY: up down logs test lint format migrate revision

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f api

test:
	docker compose run --rm api pytest

lint:
	docker compose run --rm api ruff check .
	docker compose run --rm api mypy app

format:
	docker compose run --rm api ruff format .
	docker compose run --rm api ruff check --fix .

migrate:
	docker compose run --rm api alembic upgrade head

revision:
	docker compose run --rm api alembic revision --autogenerate -m "$(m)"
