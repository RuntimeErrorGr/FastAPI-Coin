COMPOSE_DEV = docker compose -f docker-compose.yaml
COMPOSE_TEST = docker compose -f docker-compose.test.yaml

.PHONY: help \
        dev-build dev-run dev-clean dev-prune \
        test-build test-run test-clean test-prune \
		local-run

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

dev-build:
	$(COMPOSE_DEV) build

dev-run: dev-build
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