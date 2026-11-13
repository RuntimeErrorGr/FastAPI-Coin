COMPOSE_DEV = docker compose -f docker-compose.yaml
COMPOSE_TEST = docker compose -f docker-compose.test.yaml

export APP_UID := $(shell id -u)

.PHONY: help \
        dev-build dev-run dev-clean dev-prune \
        test-build test-run test-clean test-prune \
        local-test local-clean

help:
	@echo ""
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev-build   Build all dev images"
	@echo "  make dev-run     Build and run dev stack"
	@echo "  make dev-clean   Stop and remove dev containers"
	@echo "  make dev-prune   Stop and remove dev containers, images, volumes"
	@echo ""
	@echo "Testing:"
	@echo "  make test-build  Build test image"
	@echo "  make test-run    Build and run tests"
	@echo "  make test-clean  Stop and remove test containers"
	@echo "  make test-prune  Stop and remove test containers, images, volumes"
	@echo ""
	@echo "Local testing:"
	@echo "  make local-test  Run tests locally"
	@echo "  make local-clean Remove local test, coverage, log and cache artifacts"

dev-build:
	$(COMPOSE_DEV) build

dev-run: dev-build
	mkdir -p logs
	$(COMPOSE_DEV) up -d

dev-clean:
	$(COMPOSE_DEV) down

dev-prune:
	$(COMPOSE_DEV) down --rmi all --volumes --remove-orphans


test-build:
	$(COMPOSE_TEST) build

test-run: test-build
	$(COMPOSE_TEST) run --rm tests

test-clean:
	$(COMPOSE_TEST) down

test-prune:
	$(COMPOSE_TEST) down --rmi all --volumes --remove-orphans

local-test:
	uv sync --extra dev
	uv run pytest --cov --cov-report=term

local-clean:
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf logs
	find . -path ./.venv -prune -o -type d -name __pycache__ -exec rm -rf {} +