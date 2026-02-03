.PHONY: help install lint format check test clean

help:
	@echo "Available commands:"
	@echo "  install     Install dependencies"
	@echo "  lint        Run ruff linter"
	@echo "  format      Format code with ruff"
	@echo "  check       Run linter and check formatting"
	@echo "  fix         Fix linting issues automatically"
	@echo "  test        Run Django tests"
	@echo "  clean       Clean cache files"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

lint:
	ruff check .

format:
	ruff format .

check:
	ruff check .
	ruff format --check .

fix:
	ruff check --fix .
	ruff format .

test:
	python manage.py test

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".ruff_cache" -delete