PYTHON ?= python3
VENV ?= .venv
VENV_PIP := $(VENV)/bin/pip

.PHONY: setup install-dev test lint run-cycle run-demo run-plan-demo offline-consolidate sandbox-test

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -e .[dev]

install-dev:
	$(PYTHON) -m pip install -e .[dev]

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m compileall src tests

run-cycle:
	$(PYTHON) -m ree_openclaw.cli run-cycle

run-demo:
	$(PYTHON) -m ree_openclaw.cli run-demo

run-plan-demo:
	$(PYTHON) -m ree_openclaw.cli plan-demo

offline-consolidate:
	$(PYTHON) -m ree_openclaw.cli offline-consolidate

sandbox-test:
	./scripts/run_sandbox_tests.sh
