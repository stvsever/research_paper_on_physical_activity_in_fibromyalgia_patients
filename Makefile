PYTHON ?= python3.12
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python
PIPELINE := src/utils/pipeline/full/run_all.py

.PHONY: help venv install setup run-all run-stage run-from paper check docker-build docker-check clean

help:
	@echo "Targets:"
	@echo "  make setup              - create venv and install Python dependencies"
	@echo "  make run-all            - run the full analysis pipeline"
	@echo "  make run-stage STAGE=05 - run one stage prefix"
	@echo "  make run-from STAGE=05  - resume from a stage prefix"
	@echo "  make paper    - compile paper/report/main.tex with tectonic"
	@echo "  make check    - verify Python syntax and command entrypoints"
	@echo "  make docker-build       - build the Docker image"
	@echo "  make docker-check       - run make check inside Docker"
	@echo "  make clean    - remove caches and build artifacts"

venv:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip

install: venv
	$(PIP) install -e .

setup: install

run-all: install
	$(PY) $(PIPELINE)

run-stage: install
	@test -n "$(STAGE)" || (echo "Usage: make run-stage STAGE=05" && exit 2)
	$(PY) $(PIPELINE) --only $(STAGE)

run-from: install
	@test -n "$(STAGE)" || (echo "Usage: make run-from STAGE=05" && exit 2)
	$(PY) $(PIPELINE) --from $(STAGE)

paper:
	cd paper/report && tectonic --reruns 4 main.tex

check:
	$(PYTHON) -m compileall src/utils
	$(PYTHON) $(PIPELINE) --help >/dev/null
	Rscript --version >/dev/null

docker-build:
	docker compose -f docker/docker-compose.yml build

docker-check:
	docker compose -f docker/docker-compose.yml run --rm paper-analysis make check

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache
