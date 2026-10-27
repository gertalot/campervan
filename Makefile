.PHONY: setup check format chrome build serve site

setup:
	uv sync --locked
	npm --prefix frontend ci

check:
	uv run --locked ruff check src
	uv run --locked ruff format --check src
	uv run --locked mypy
	npm --prefix frontend run check

format:
	uv run --locked ruff format src

build:
	npm --prefix frontend run build
	uv build

site:
	uv run --locked campervan site

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
