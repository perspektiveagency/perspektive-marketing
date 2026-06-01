.PHONY: install test lint demo companies

install:
	pip install -e ".[dev,all]"

test:
	pytest

lint:
	ruff check .

# End-to-end run with no API calls (writes placeholder assets).
demo:
	perspektive generate acme-co summer-launch --dry-run

companies:
	perspektive companies
