VENV_DIR := $(HOME)/dev/.venvs/hermes-a2a
PYTHON   := $(VENV_DIR)/bin/python
UV       := uv

.PHONY: init start stop restart test clean

init:
	mkdir -p $(VENV_DIR)
	$(UV) venv $(VENV_DIR) --python 3.11
	ln -sfn $(VENV_DIR) .venv
	$(UV) pip install -e ".[dev]" --python $(VENV_DIR)/bin/python
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example — set HERMES_API_KEY before starting"; fi

start:
	$(PYTHON) -m hermes_a2a

stop:
	pkill -f "python -m hermes_a2a" || true

restart: stop start

test:
	$(UV) run --python $(VENV_DIR)/bin/python pytest tests/ -v

clean:
	rm -rf __pycache__ hermes_a2a/__pycache__ tests/__pycache__ .pytest_cache dist *.egg-info
