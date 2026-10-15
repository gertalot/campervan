.PHONY: setup check test test-ui format chrome build serve

setup:
	uv sync --locked
	npm --prefix frontend ci

check:
	uv run --locked ruff check src tests
	uv run --locked ruff format --check src tests
	uv run --locked mypy
	npm --prefix frontend run check

test:
	uv run --locked pytest
	npm --prefix frontend test

test-ui:
	npm --prefix frontend test

format:
	uv run --locked ruff format src tests

build:
	npm --prefix frontend run build
	uv build

serve:
	mkdir -p logs
	bash -o pipefail -c 'PYTHONUNBUFFERED=1 uv run --locked campervan serve 2>&1 | tee logs/api.log'

chrome:
	bash scripts/launch-chrome.sh

.PHONY: viewer dev-api dev-ui

viewer:
	mkdir -p logs
	bash -o pipefail -c 'PYTHONUNBUFFERED=1 uv run --locked campervan viewer 2>&1 | tee logs/viewer.log'

dev-api:
	mkdir -p logs
	bash -o pipefail -c 'PYTHONUNBUFFERED=1 uv run --locked campervan dev-api 2>&1 | tee logs/api.log'

dev-ui:
	mkdir -p logs
	bash -o pipefail -c 'uv run --locked campervan dev-ui 2>&1 | tee logs/ui.log'
