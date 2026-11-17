.PHONY: setup run worker beat test seed lint migrate makemigrations clean

PYTHON ?= ./venv/bin/python
PIP ?= ./venv/bin/pip
PYTEST ?= ./venv/bin/pytest
RUFF ?= ./venv/bin/ruff

setup:
	$(PIP) install -r requirements/dev.txt
	$(PYTHON) manage.py migrate
	$(PYTHON) manage.py seed_demo_data

run:
	$(PYTHON) manage.py runserver 0.0.0.0:8000

worker:
	celery -A config worker -l info

beat:
	celery -A config beat -l info

test:
	$(PYTEST) tests/

lint:
	$(RUFF) check .

seed:
	$(PYTHON) manage.py seed_demo_data

migrate:
	$(PYTHON) manage.py migrate

makemigrations:
	$(PYTHON) manage.py makemigrations

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
