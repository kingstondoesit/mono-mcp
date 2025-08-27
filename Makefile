.PHONY: help test test-unit test-integration test-performance test-all lint format type-check security install clean build ci

help:  ## show help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n"} /^[$$()% a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Testing
test: test-unit  ## run all unit tests
	@echo "✅ Unit tests completed"

test-unit:  ## run unit tests only
	pytest tests/ -v -m "not integration and not performance" --cov=mono_banking_mcp --cov-report=term-missing

test-integration:  ## run integration tests (requires MONO_SECRET_KEY)
	pytest tests/ -v -m integration --tb=short

test-performance:  ## run performance tests
	pytest tests/ -v -m performance --tb=short

test-all:  ## run all tests including integration and performance
	pytest tests/ -v --cov=mono_banking_mcp --cov-report=html --cov-report=term

##@ Code Quality
lint:  ## run linting checks
	ruff check mono_banking_mcp/ tests/

format:  ## format code with black
	black mono_banking_mcp/ tests/

format-check:  ## check code formatting
	black --check mono_banking_mcp/ tests/

type-check:  ## run type checking
	mypy mono_banking_mcp/ --ignore-missing-imports

security:  ## run security scans
	bandit -r mono_banking_mcp/
	safety check

##@ Development
install:  ## install dependencies
	pip install -r requirements.txt

install-dev:  ## install development dependencies
	pip install -r requirements.txt
	pip install -e .

clean:  ## clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

##@ Build & Release
build:  ## build package
	python -m build

ci:  ## run full CI pipeline locally
	@echo "🔍 Running linting..."
	@make lint
	@echo "🎨 Checking formatting..."
	@make format-check
	@echo "🔍 Running type checking..."
	@make type-check
	@echo "🧪 Running tests..."
	@make test-unit
	@echo "🔒 Running security scans..."
	@make security
	@echo "✅ All CI checks passed!"

##@ MCP Server
server:  ## run MCP server for testing
	python -m mono_banking_mcp.server

server-debug:  ## run MCP server with debug logging
	PYTHONPATH=. python -c "import logging; logging.basicConfig(level=logging.DEBUG); from mono_banking_mcp.server import main; main()"

tools:  ## list available MCP tools
	python -c "import asyncio; from mono_banking_mcp.server import mcp; print('Available tools:'); [print(f'- {tool.name}: {tool.description}') for tool in asyncio.run(mcp.list_tools())]"
