.PHONY: setup dev build lint-all test-all seed seed-prod prod clean help

## First-time local setup (run once after clone)
setup:
	bash scripts/dev-setup.sh

## Start all dev servers: API + UI + CRDT. Ctrl-C stops all.
dev:
	@( \
		trap 'kill 0; exit' INT TERM; \
		(cd api && DJANGO_SETTINGS_MODULE=papadapi.config.local \
		  .venv/bin/python manage.py runserver 2>&1 | sed 's/^/[api]  /') & \
		(cd ui && npm run dev 2>&1 | sed 's/^/[ui]   /') & \
		(cd crdt && npm run dev 2>&1 | sed 's/^/[crdt] /') & \
		wait \
	)

## Build the SvelteKit SPA (required before deploying)
build:
	cd ui && npm install && npm run build

## Run all linters across api/ and ui/
lint-all:
	cd api && make lint-full
	cd ui && npm run lint && npm run check

## Run all tests across api/ and ui/
test-all:
	cd api && make test
	cd ui && npm run test:all

## Seed dev database (admin/admin + demo/demo + Demo Community)
seed:
	cd api && DJANGO_SETTINGS_MODULE=papadapi.config.local \
	  .venv/bin/python manage.py seed_dev

## Create production admin user (requires ADMIN_PASSWORD env var)
seed-prod:
	cd api && DJANGO_SETTINGS_MODULE=papadapi.config.production \
	  .venv/bin/python manage.py seed_prod

## Build UI + start full production stack
prod:
	cd ui && npm install && npm run build
	docker compose -f deploy/docker-compose.yml up -d --build

## Remove all build artefacts
clean:
	cd ui && rm -rf build .svelte-kit
	cd crdt && rm -rf dist

## Show available targets
help:
	@echo "  setup      First-time local setup (run once after clone)"
	@echo "  dev        Start API + UI + CRDT dev servers. Ctrl-C stops all."
	@echo "  build      Build the SvelteKit SPA (required before deploying)"
	@echo "  lint-all   Run all linters across api/ and ui/"
	@echo "  test-all   Run all tests across api/ and ui/"
	@echo "  seed       Seed dev database (admin/admin, demo/demo, tags)"
	@echo "  seed-prod  Seed production (requires ADMIN_PASSWORD env var)"
	@echo "  prod       Build UI + start production Docker stack"
	@echo "  clean      Remove build artefacts"
