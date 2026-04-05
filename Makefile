PYTHON ?= $(if $(wildcard .venv/bin/python),./.venv/bin/python,python3)
PIP ?= $(PYTHON) -m pip
MKDOCS ?= $(if $(wildcard .venv/bin/mkdocs),./.venv/bin/mkdocs,mkdocs)

DOCS_DATA := docs/assets/data/docs_data.json

.PHONY: help docs-clear docs-generate docs-build docs-serve docs-install

help:
	@echo "Targets:"
	@echo "  make docs-clear      Remove generated docs payload and built site"
	@echo "  make docs-generate   Rebuild docs/assets/data/docs_data.json"
	@echo "  make docs-build      Rebuild docs data and build the MkDocs site"
	@echo "  make docs-serve      Rebuild docs data and serve the MkDocs site locally"
	@echo "  make docs-install    Install docs dependencies into the current Python env"

docs-clear:
	rm -f $(DOCS_DATA)
	rm -rf site

docs-generate:
	$(PYTHON) scripts/build_docs_data.py

docs-build: docs-generate
	$(MKDOCS) build

docs-serve: docs-generate
	$(MKDOCS) serve

docs-install:
	$(PIP) install -e '.[docs]'
