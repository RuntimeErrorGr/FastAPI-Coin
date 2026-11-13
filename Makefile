COMPOSE_DEV = docker compose -f docker-compose.yaml
COMPOSE_TEST = docker compose -f docker-compose.test.yaml

export APP_UID := $(shell id -u)

.PHONY: help \
        dev-build dev-run dev-clean dev-prune \
        db-upgrade db-downgrade db-revision db-shell \
        test-build test-run test-clean test-prune \
        lock local-clean

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
	@echo "Database:"
	@echo "  make db-upgrade                   Apply all pending migrations"
	@echo "  make db-downgrade                 Revert the latest migration"
	@echo "  make db-revision m=\"...\" id=...   Create an empty migration (e.g. m=\"add doge\" id=0003)"
	@echo "  make db-shell                     Open a psql shell on the dev database"
	@echo ""
	@echo "Testing:"
	@echo "  make test-build  Build test image"
	@echo "  make test-run    Build and run tests, then remove the test stack"
	@echo "  make test-clean  Stop and remove test containers"
	@echo "  make test-prune  Stop and remove test containers, images, volumes"
	@echo ""
	@echo "Other:"
	@echo "  make lock        Regenerate uv.lock after editing pyproject.toml"
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


db-upgrade:
	$(COMPOSE_DEV) run --rm migrate upgrade head

db-downgrade:
	$(COMPOSE_DEV) run --rm migrate downgrade -1

db-revision:
	@test -n "$(m)" -a -n "$(id)" || (echo 'Usage: make db-revision m="add doge" id=0003' && exit 1)
	$(COMPOSE_DEV) run --rm migrate revision -m "$(m)" --rev-id $(id)

db-shell:
	$(COMPOSE_DEV) exec postgres sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'


test-build:
	$(COMPOSE_TEST) build

test-run: test-build
	$(COMPOSE_TEST) run --rm tests; status=$$?; $(COMPOSE_TEST) down; exit $$status

test-clean:
	$(COMPOSE_TEST) down

test-prune:
	$(COMPOSE_TEST) down --rmi all --volumes --remove-orphans

lock:
	docker build -q --target base --build-arg APP_UID=$(APP_UID) -t coinapi/base .
	docker run --rm --user "$$(id -u):$$(id -g)" -e UV_CACHE_DIR=/tmp/uv-cache \
		-v "$(CURDIR)":/app -w /app coinapi/base uv lock

local-clean:
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf logs
	find . -path ./.venv -prune -o -type d -name __pycache__ -exec rm -rf {} +