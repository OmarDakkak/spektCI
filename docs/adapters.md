# Platform Adapter Development Guide

This guide explains how to add a new CI/CD platform adapter to spektci.

## Architecture

Each platform adapter consists of three components:

```
adapters/<platform>/
├── __init__.py
├── adapter.py      # Orchestrates collection + parsing
├── collector.py    # API client / file reader
└── parser.py       # Normalizes raw data → PipelineModel
```

## Step 1: Create the adapter package

Create a new directory under `src/spektci/adapters/` with the platform name.

## Step 2: Implement `BasePlatformAdapter`

Your adapter must implement the abstract methods defined in `BasePlatformAdapter`:

```python
from spektci.adapters.base import BasePlatformAdapter, RawPipelineData
from spektci.core.models import BranchProtection, PipelineModel

class MyPlatformAdapter(BasePlatformAdapter):
    def detect(self, remote_url: str) -> bool:
        """Return True if this adapter handles the given git remote."""
        return "myplatform.com" in remote_url

    def collect(self, config) -> RawPipelineData:
        """Fetch pipeline configs from API or local files."""
        ...

    def parse(self, raw: RawPipelineData) -> PipelineModel:
        """Convert raw data into the common PipelineModel."""
        ...

    def get_branch_protection(self, branch: str) -> BranchProtection:
        """Fetch branch protection rules."""
        ...
```

## Step 3: Register the adapter

Add your adapter to:

1. `src/spektci/adapters/__init__.py` — in the `get_adapter()` function
2. `src/spektci/adapters/detector.py` — add URL pattern for auto-detection

## Step 4: Implement the collector

The collector is responsible for:

- Fetching pipeline configuration files (from API or local filesystem)
- Fetching repository metadata
- Returning a `RawPipelineData` instance

## Step 5: Implement the parser

The parser normalizes platform-specific data into the common `PipelineModel`:

- Parse pipeline config files into stages, steps, and actions
- Extract container image references
- Extract action/plugin/orb references
- Extract permission settings

## Step 6: Write tests

- Create test fixtures under `tests/fixtures/<platform>/`
- Write unit tests under `tests/unit/test_adapters/`
- Test both the parser and collector independently

## Key data types to populate

| PipelineModel field | What to populate |
|--------------------|-----------------|
| `stages` | Jobs/stages with their steps |
| `images` | All container image references |
| `actions` | All external action/plugin/orb references |
| `permissions` | Workflow-level permission settings |
| `raw_content` | Raw file contents (for secret scanning) |
| `branch_protections` | Branch protection rules |
