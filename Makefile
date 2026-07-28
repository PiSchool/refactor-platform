# One entry point per surface. CI runs these same targets, so a check that
# passes here passes there.
#
#   make check                     everything below, in order
#   make plugin PLUGIN=path/to/it  your own plugin against the contracts
#
# The server environment is managed by uv, as the image and CI are. Without uv
# on PATH, an environment at server/.venv is used instead.

SHELL := /bin/bash
UV := $(shell command -v uv 2>/dev/null)
ifeq ($(UV),)
SERVER_PY := .venv/bin/python
else
SERVER_PY := uv run --frozen python
endif

# A pgvector database exercises the retrieval tests. Without these, those tests
# skip and the rest of the suite still runs.
RETRIEVAL_TEST_DATABASE_URL ?=
PLATFORM_TEST_DATABASE_URL ?=
export RETRIEVAL_TEST_DATABASE_URL PLATFORM_TEST_DATABASE_URL

.DEFAULT_GOAL := help
.PHONY: help install check backend plugins plugin web types build browser docs

help:
	@echo "Targets:"
	@grep -hE '^[a-z][a-z-]*:.*## ' $(MAKEFILE_LIST) \
	  | sed -E 's/:.*## /\t/' | expand -t 12 | sed 's/^/  /'

install: ## Install the server and dashboard dependencies
	cd server && $(if $(UV),uv sync --frozen --group dev,python3 -m venv .venv && .venv/bin/pip install -e '.[postgres]')
	cd web && npm ci

check: backend plugins web types build docs ## Run every check a change must pass
	@echo "all checks passed"

backend: ## Server tests
	cd server && $(SERVER_PY) -m pytest -q

plugins: ## Every shipped plugin against the contracts
	cd server && $(SERVER_PY) -m app.catalog.verify --plugins-dir ../plugins

plugin: ## One plugin against the contracts: make plugin PLUGIN=plugins/benchmarks/mine
	@test -n "$(PLUGIN)" || { echo "usage: make plugin PLUGIN=<directory>"; exit 2; }
	cd server && $(SERVER_PY) -m app.catalog.verify --plugins-dir ../plugins "$(abspath $(PLUGIN))"

web: ## Dashboard tests
	cd web && npm test

types: ## Dashboard type check
	cd web && npx tsc --noEmit

build: ## Dashboard production build
	cd web && npm run build

browser: ## Dashboard workflow in a real browser, against a real API
	@cd web && node scripts/browser-preflight.mjs; \
	case $$? in \
	  0) npm run test:e2e ;; \
	  3) exit 0 ;; \
	  *) exit 1 ;; \
	esac

docs: ## Every link, anchor and figure in the documentation
	python3 scripts/check_docs.py
