.PHONY: install test lint fmt run up down build helm-lint ci

PYTHON ?= python3

install:
	$(PYTHON) -m pip install -e "./backend[dev]"
	npm --prefix frontend install

test:
	$(PYTHON) -m pytest backend/tests

lint:
	$(PYTHON) -m ruff check backend
	$(PYTHON) -m ruff format --check backend

fmt:
	$(PYTHON) -m ruff check --fix backend
	$(PYTHON) -m ruff format backend

run:
	cd backend && DATABASE_URL=sqlite+pysqlite:///./leaflet.db AUTO_CREATE_SCHEMA=true SEED_DEMO=true REDIS_URL= \
		$(PYTHON) -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

up:
	docker compose up --build

down:
	docker compose down -v

build:
	docker build -t leaflet-api:local backend
	docker build -t leaflet-web:local frontend

helm-lint:
	helm lint deploy/helm/leaflet

ci: lint test
	npm --prefix frontend ci
	npm --prefix frontend run build
