PYTHON ?= $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)

.PHONY: lint typecheck test check

lint:
	$(PYTHON) -m ruff check .

typecheck:
	$(PYTHON) -m mypy

test:
	PYQT_TESTS=1 $(PYTHON) -m pytest

check: lint typecheck test
