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
	@if launchctl list 2>/dev/null | grep -q $(LABEL); then \
		echo "hermes-a2a is already running (launchd service)"; \
	elif [ -f $(PLIST) ]; then \
		echo "Starting hermes-a2a (launchd)..."; \
		launchctl load -w $(PLIST); \
		sleep 1; \
		if launchctl list 2>/dev/null | grep -q $(LABEL); then \
			echo "hermes-a2a started"; \
		else \
			echo "hermes-a2a failed to start — check logs/hermes-a2a.error.log"; \
		fi; \
	else \
		$(PYTHON) -m hermes_a2a; \
	fi

stop:
	@if launchctl list 2>/dev/null | grep -q $(LABEL); then \
		echo "Stopping hermes-a2a (launchd)..."; \
		launchctl unload $(PLIST); \
		echo "hermes-a2a stopped"; \
	elif pgrep -f "python -m hermes_a2a" > /dev/null 2>&1; then \
		echo "Stopping hermes-a2a..."; \
		pkill -f "python -m hermes_a2a"; \
		echo "hermes-a2a stopped"; \
	else \
		echo "hermes-a2a is not running"; \
	fi

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
