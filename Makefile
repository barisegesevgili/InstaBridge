.PHONY: help install test lint format clean run

help:
	@echo "InstaToWhatsapp - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install     Install dependencies"
	@echo "  make install-dev Install dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test        Run tests"
	@echo "  make test-cov    Run tests with coverage"
	@echo "  make lint        Run linters"
	@echo "  make format      Format code"
	@echo "  make typecheck   Run type checker"
	@echo ""
	@echo "Running:"
	@echo "  make run         Run once"
	@echo "  make scheduler   Start scheduler"
	@echo "  make webapp      Start web UI"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean       Clean generated files"

install:
	pip install -r requirements.txt
	python -m playwright install chromium

install-dev:
	pip install -r requirements-dev.txt
	python -m playwright install chromium

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

lint:
	ruff check src/ tests/
	black --check src/ tests/

format:
	black src/ tests/
	ruff check --fix src/ tests/

typecheck:
	mypy src/

run:
	python -m src.main

scheduler:
	python -m src.scheduler

webapp:
	python -m src.webapp

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov
	rm -f .coverage coverage.xml
