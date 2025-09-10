.PHONY: lint fmt type test cov docs

lint:
	poetry run ruff check .
	poetry run black --check .
	poetry run interrogate -v

fmt:
	poetry run ruff check . --fix
	poetry run black .

type:
	poetry run mypy src

test:
	poetry run pytest -q

cov:
	poetry run pytest --cov=src --cov-report=term-missing --cov-report=xml

docs:
	poetry run mkdocs build
