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

.PHONY: scan-native
scan-native:
	@if [ ! -x .local/native-rtabmap/build-tools/bin/python ]; then \
		uv venv --python 3.13 .local/native-rtabmap/build-tools; \
	fi
	@if [ ! -x .local/native-rtabmap/build-tools/bin/cmake ] || [ ! -x .local/native-rtabmap/build-tools/bin/ninja ] || \
		[ ! -d .local/native-rtabmap/build-tools/lib/python3.13/site-packages/scikit_build_core ]; then \
		uv pip install --python .local/native-rtabmap/build-tools/bin/python \
			scikit-build-core==0.11.6 cmake==3.31.6 ninja==1.11.1.1; \
	fi
	PATH="$(CURDIR)/.local/native-rtabmap/build-tools/bin:$$(dirname "$$(command -v uv)"):/usr/bin:/bin:/usr/sbin:/sbin" \
	CMAKE_EXECUTABLE="$(CURDIR)/.local/native-rtabmap/build-tools/lib/python3.13/site-packages/cmake/data/bin/cmake" \
	CMAKE_ARGS="-DCMAKE_MAKE_PROGRAM=$(CURDIR)/.local/native-rtabmap/build-tools/lib/python3.13/site-packages/ninja/data/bin/ninja" \
	UV_NO_BUILD_ISOLATION=1 UV_PYTHON="$(CURDIR)/.local/native-rtabmap/build-tools/bin/python" \
	CMAKE_BUILD_PARALLEL_LEVEL=2 uv build native/rtabmap --wheel --out-dir .local/native-rtabmap/wheels
