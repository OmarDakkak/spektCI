# Contributing to spektci

Thank you for your interest in contributing to **spektci**! This document provides guidelines for contributing.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/spektci/spektci.git
cd spektci

# Create a virtual environment
python -m venv .venv && source .venv/bin/activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

## Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run a specific test file
pytest tests/unit/test_controls/test_image_tags.py -v
```

## Code Quality

```bash
# Lint + format check
make lint

# Auto-fix lint issues + format
make format

# Type checking
make typecheck
```

## Project Structure

- **`src/spektci/core/`** — Core models (`PipelineModel`, `Finding`, etc.) and the analysis engine.
- **`src/spektci/config/`** — Pydantic configuration schema, YAML loader, and default config generator.
- **`src/spektci/cli/`** — Click command definitions.
- **`src/spektci/controls/`** — Compliance controls (C001–C008). Each control is a self-contained module.
- **`src/spektci/adapters/`** — Platform adapters. Each platform has its own sub-package.
- **`src/spektci/reporters/`** — Output formatters (terminal, JSON, SARIF).
- **`tests/`** — Unit and integration tests, organized to mirror `src/`.

## Adding a New Control

1. Create a new file in `src/spektci/controls/` (e.g., `my_control.py`).
2. Subclass `BaseControl` and implement `evaluate()`.
3. Register the control in `src/spektci/controls/registry.py`.
4. Add config schema fields in `src/spektci/config/schema.py`.
5. Add default config values in `src/spektci/config/defaults.py`.
6. Write tests in `tests/unit/test_controls/`.
7. Document in `docs/controls.md`.

## Adding a New Platform Adapter

1. Create a new sub-package under `src/spektci/adapters/` (e.g., `gitlab/`).
2. Implement `adapter.py` (subclass `BasePlatformAdapter`), `collector.py`, and `parser.py`.
3. Register the adapter in `src/spektci/adapters/__init__.py`.
4. Add detection logic in `src/spektci/adapters/detector.py`.
5. Create test fixtures in `tests/fixtures/<platform>/`.
6. Write tests in `tests/unit/test_adapters/`.

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation
- `test:` — adding or updating tests
- `refactor:` — code restructuring without behavior change
- `chore:` — maintenance tasks

## Pull Request Process

1. Fork the repo and create a feature branch.
2. Write tests for your changes.
3. Ensure `make lint` and `make test` pass.
4. Open a PR with a clear description of your changes.

## License

By contributing, you agree that your contributions will be licensed under the MPL-2.0 license.
