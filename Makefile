.PHONY: help install dev-install test lint format clean docker-build docker-run

help:
	@echo "Data Profiler - Makefile Commands"
	@echo ""
	@echo "  install        Install package"
	@echo "  dev-install    Install package with dev dependencies"
	@echo "  test           Run tests"
	@echo "  test-cov       Run tests with coverage"
	@echo "  lint           Run linters"
	@echo "  format         Format code"
	@echo "  clean          Clean build artifacts"
	@echo "  docker-build   Build Docker image"
	@echo "  docker-run     Run Docker container"
	@echo "  serve          Run API server locally"

install:
	pip install -e .

dev-install:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest -v

test-cov:
	pytest --cov=src/data_profiler --cov-report=html --cov-report=term

benchmark:
	pytest tests/test_performance.py -v

lint:
	ruff check src/ tests/
	mypy src/

format:
	black src/ tests/
	ruff check --fix src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/

docker-build:
	docker build -t data-profiler:latest .

docker-run:
	docker run -p 8000:8000 data-profiler:latest

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

serve:
	uvicorn data_profiler.api.main:app --reload --host 0.0.0.0 --port 8000
