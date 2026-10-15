.PHONY: setup check test test-ui format chrome

setup:
	uv sync --locked
	npm --prefix frontend ci

check:
	uv run --locked ruff check .
	uv run --locked ruff format --check .
	uv run --locked mypy
	npm --prefix frontend run check

test:
	uv run --locked pytest

test-ui:
	npm --prefix frontend test

format:
	uv run --locked ruff format .

chrome:
	bash scripts/launch-chrome.sh

.PHONY: viewer dev-api dev-ui

viewer:
	uv run --locked campervan viewer

dev-api:
	uv run --locked campervan dev-api

dev-ui:
	uv run --locked campervan dev-ui
