.PHONY: help quickstart test test-api lint format clean install run-api canary-deploy canary-promote rollback-llm

help:
	@echo "AstroML Development Commands"
	@echo "============================"
	@echo ""
	@echo "make quickstart          Run quick start: ingestion → graph → train pipeline"
	@echo "make quickstart-verbose  Run quick start with verbose output"
	@echo "make test                Run full test suite"
	@echo "make test-api            Run API integration tests only"
	@echo "make lint                Run linters (flake8, mypy)"
	@echo "make format              Format code (black, isort)"
	@echo "make install             Install development dependencies"
	@echo "make clean               Clean build artifacts and cache"
	@echo "make run-api             Start the FastAPI dev server on localhost:8000"
	@echo "make canary-deploy       Deploy LLM canary to Kubernetes"
	@echo "make canary-promote      Promote canary to stable"
	@echo "make rollback-llm        Rollback LLM canary deployment"
	@echo ""

quickstart:
	python -m astroml.quick_start

quickstart-verbose:
	python -m astroml.quick_start --num-ledgers 200 --num-accounts 100 --epochs 20

test:
	pytest tests/ -v

test-api:
	pytest api/tests/ -v --tb=short

lint:
	flake8 astroml/ tests/
	mypy astroml/ --ignore-missing-imports

format:
	black astroml/ tests/
	isort astroml/ tests/

run-api:
	uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload

install:
	pip install -e ".[dev]"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache build/ dist/ *.egg-info
	rm -rf benchmark_results/quickstart .astroml_state_quickstart

install:
	pip install -e "[dev]"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache build/ dist/ *.egg-info
	rm -rf benchmark_results/quickstart .astroml_state_quickstart

# Dev setup target – start full stack, seed data, run health checks
.PHONY: dev-setup
dev-setup:
	@echo "🚀 Starting local development environment…"
	@docker compose -f docker-compose.yml up -d --build
	@./scripts/seed_data.sh
	@./scripts/health_check.sh
	@echo "✅ Development environment ready."

.PHONY: canary-deploy
canary-deploy:
	@echo "🚀 Deploying LLM canary..."
	REGISTRY=$(shell grep -E '^REGISTRY' .github/workflows/llm-cicd.yml | head -n1 | sed 's/.*: //' | tr -d '"')
	IMAGE_TAG=llm-$(shell git rev-parse --short HEAD)
	REPO=$(shell basename $$(pwd))
	NAMESPACE=astroml ./scripts/canary-deploy.sh

.PHONY: canary-promote
canary-promote:
	@echo "✅ Promoting canary to stable..."
	REGISTRY=$(shell grep -E '^REGISTRY' .github/workflows/llm-cicd.yml | head -n1 | sed 's/.*: //' | tr -d '"')
	IMAGE_TAG=llm-$(shell git rev-parse --short HEAD)
	REPO=$(shell basename $$(pwd))
	NAMESPACE=astroml ./scripts/canary-promote.sh

.PHONY: rollback-llm
rollback-llm:
	@echo "🔄 Rolling back LLM deployment..."
	NAMESPACE=astroml STABLE_DEPLOYMENT=astroml-api ./scripts/auto-rollback.sh
