.PHONY: validate validate-soft validate-smoke daily status smoke health install

PYTHON ?= python3
BASE ?= $(CURDIR)
SCRIPTS := $(BASE)/scripts
PKG := newsletter-ai

# Legacy validate targets (now point to legacy scripts with deprecation warning)
validate:
	@echo "[DEPRECATION] validate now uses legacy/v0.1/scripts/validate_release.py"
	$(PYTHON) legacy/v0.1/scripts/validate_release.py

validate-soft:
	@echo "[DEPRECATION] validate-soft now uses legacy/v0.1/scripts/validate_release.py"
	$(PYTHON) legacy/v0.1/scripts/validate_release.py --soft-exit

validate-smoke:
	@echo "[DEPRECATION] validate-smoke now uses legacy/v0.1/scripts/validate_release.py"
	$(PYTHON) legacy/v0.1/scripts/validate_release.py --with-feedback-smoke

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