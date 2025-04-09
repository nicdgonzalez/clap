.PHONY: install test docs type-check

install:
	python3 -m pip install .

test:
	python3 -m unittest

docs:
	mkdocs serve --dev-addr 0.0.0.0:5000

type-check:
	mypy --strict ./src
