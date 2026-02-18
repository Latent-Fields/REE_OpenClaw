PYTHON ?= python3
VENV ?= .venv
VENV_PIP := $(VENV)/bin/pip

.PHONY: setup install-dev test lint run-cycle run-demo sandbox-test

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

sandbox-test:
	./scripts/run_sandbox_tests.sh
