.PHONY: help dev dev-backend dev-frontend test test-backend test-frontend lint migrate migrate-down migration seed update-market-data

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev: ## Start all services with docker-compose
	docker compose up

dev-backend: ## Start backend dev server
	cd backend && uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend dev server
	cd frontend && bun run dev

test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests
	cd backend && python -m pytest

test-frontend: ## Run frontend tests
	cd frontend && bun test

lint: ## Run linters
	cd backend && ruff check src tests
	cd frontend && bun run lint

migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-down: ## Rollback last migration
	cd backend && alembic downgrade -1

migration: ## Create new migration (usage: make migration msg="description")
	cd backend && alembic revision --autogenerate -m "$(msg)"

seed: ## Seed database with initial data
	cd backend && python -m src.app.scripts.seed

update-market-data: ## Update market data from external sources
	cd backend && python -m src.app.cli update-market-data
