.PHONY: all help fmt typecheck test install

all: fmt typecheck test

help:
	@cat Makefile | grep -E "^\w+:"

fmt: pyproject.toml
	@echo "===> FORMATTING"
	@isort .
	@black .

typecheck:
	@echo "===> TYPE CHECKING"
	@mypy --strict --exclude="_[^_]+\.py" clap

test:
	@echo "===> TESTING"
	@python -m unittest discover -s tests

install: pyproject.toml setup.py
	@echo "===> INSTALLING"
	@python -m pip install .
