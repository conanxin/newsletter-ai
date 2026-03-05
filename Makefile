.PHONY: validate validate-soft validate-smoke daily status

PYTHON ?= python3
BASE := /mnt/d/obsidian_nov/nov/newsletter
SCRIPTS := $(BASE)/scripts

validate:
	$(PYTHON) $(SCRIPTS)/validate_release.py

validate-soft:
	$(PYTHON) $(SCRIPTS)/validate_release.py --soft-exit

validate-smoke:
	$(PYTHON) $(SCRIPTS)/validate_release.py --with-feedback-smoke

daily:
	$(PYTHON) $(SCRIPTS)/run_daily_pipeline.py

status:
	$(PYTHON) $(SCRIPTS)/check_pipeline_status.py
