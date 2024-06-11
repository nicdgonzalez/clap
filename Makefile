.PHONY: install test docs

install:
	python3 -m pip install .

test:
	python3 -m unittest

docs:
	mkdocs serve --dev-addr 0.0.0.0:5000
