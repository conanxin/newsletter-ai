.PHONY: validate validate-soft validate-smoke daily status smoke health install legacy-validate

PYTHON ?= python3
BASE ?= $(CURDIR)
SCRIPTS := $(BASE)/scripts
PKG := newsletter-ai

validate:
	$(PKG) health

validate-soft:
	$(PKG) status

validate-smoke:
	$(PKG) daily --dry-run

daily:
	$(PKG) daily

status:
	$(PKG) status

smoke:
	$(PKG) daily --dry-run

health:
	$(PKG) health

install:
	$(PYTHON) -m pip install -e .[dev]

legacy-validate:
	@echo "[DEPRECATION WARNING] legacy-validate uses legacy/v0.1/scripts/"
	$(PYTHON) legacy/v0.1/scripts/validate_release.py || true