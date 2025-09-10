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





.PHONY: build sh test lint type docs

build:
	docker compose build

sh:
	docker compose run --rm dev bash

test:
	docker compose run --rm test

lint:
	docker compose run --rm dev bash -lc "ruff check . && black --check ."

type:
	docker compose run --rm dev bash -lc "mypy src"

docs:
	docker compose run --rm dev bash -lc "mkdocs build --strict"

