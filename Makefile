.PHONY: install dev test lint typecheck format dogfood clean build docker

# ── Install ──────────────────────────────────────────────────────
install:
	pip install -e .

dev:
	pip install -e ".[dev]"

# ── Quality ──────────────────────────────────────────────────────
test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --tb=short --cov=spektci --cov-report=term-missing

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

typecheck:
	mypy src/spektci/

format:
	ruff check --fix src/ tests/
	ruff format src/ tests/

# ── Dogfooding ───────────────────────────────────────────────────
dogfood:
	python -m spektci analyze --platform github

# ── Build ────────────────────────────────────────────────────────
build:
	python -m build

docker:
	docker build -t spektci:local .

# ── Cleanup ──────────────────────────────────────────────────────
clean:
	rm -rf dist/ build/ *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
