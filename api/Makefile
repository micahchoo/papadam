## papadam/api — local development helpers
## All commands use .venv (created by `make install`).

VENV   = .venv
PYTHON = $(VENV)/bin/python
PIP    = $(VENV)/bin/pip
RUFF   = $(VENV)/bin/ruff
MYPY   = $(VENV)/bin/mypy
PYTEST = $(VENV)/bin/pytest
LINT   = $(VENV)/bin/lint-imports
BANDIT = $(VENV)/bin/bandit

.PHONY: install upgrade lint lint-arch lint-full test test-cov clean help

# ── setup ──────────────────────────────────────────────────────────────────────

install: ## Create .venv and install all dev + test dependencies
	python3 -m venv $(VENV)
	$(PIP) install --quiet --upgrade pip
	$(PIP) install --quiet -r requirements/requirements-dev.txt
	$(PIP) install --quiet -r requirements/requirements-test.txt
	@echo "venv ready — activate with: source $(VENV)/bin/activate"

upgrade: ## Upgrade all pinned packages in-place
	$(PIP) install --quiet --upgrade -r requirements/requirements-dev.txt
	$(PIP) install --quiet --upgrade -r requirements/requirements-test.txt

# ── lint ───────────────────────────────────────────────────────────────────────

lint: ## ruff on new apps (strict — CI equivalent)
	$(RUFF) check papadapi/annotate papadapi/archive papadapi/importexport \
	              papadapi/crdt papadapi/events papadapi/exhibit papadapi/media_relation \
	              papadapi/queue.py papadapi/worker.py

lint-arch: ## import-linter — architecture contract check (whole codebase)
	$(LINT)

lint-full: lint lint-arch ## ruff + import-linter

# ── test ───────────────────────────────────────────────────────────────────────

test: ## Run pytest (fast — no coverage)
	DJANGO_SETTINGS_MODULE=papadapi.config.test $(PYTEST) -x -q

test-cov: ## Run pytest with coverage gate (80%)
	DJANGO_SETTINGS_MODULE=papadapi.config.test $(PYTEST) --cov=papadapi --cov-fail-under=80 -q

# ── clean ──────────────────────────────────────────────────────────────────────

clean: ## Remove venv, cache dirs
	rm -rf $(VENV) .ruff_cache .mypy_cache .import_linter_cache \
	       .pytest_cache papadapi/__pycache__ .coverage htmlcov

# ── help ───────────────────────────────────────────────────────────────────────

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'
