VENV_DIR  := $(HOME)/dev/.venvs/hermes-a2a
PYTHON    := $(VENV_DIR)/bin/python
UV        := uv
PLIST     := $(HOME)/Library/LaunchAgents/com.dave.hermes-a2a.plist
LABEL     := com.dave.hermes-a2a

.PHONY: init start stop restart test clean service-load service-unload service-start service-stop service-restart logs

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

# ── launchd service management ─────────────────────────────────────────────
service-load:
	mkdir -p logs
	launchctl load -w $(PLIST)

service-unload:
	launchctl unload $(PLIST)

service-start:
	launchctl start $(LABEL)

service-stop:
	launchctl stop $(LABEL)

service-restart:
	launchctl stop $(LABEL) && sleep 1 && launchctl start $(LABEL)

logs:
	tail -f logs/hermes-a2a.log
