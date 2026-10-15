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
	uv run --locked campervan serve

chrome:
	bash scripts/launch-chrome.sh

.PHONY: viewer dev-api dev-ui

viewer:
	uv run --locked campervan viewer

dev-api:
	uv run --locked campervan dev-api

dev-ui:
	uv run --locked campervan dev-ui
