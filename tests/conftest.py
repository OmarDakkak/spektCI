"""Shared test fixtures for spektci tests."""

from __future__ import annotations

import pytest

from spektci.config.schema import SpektciConfig
from spektci.core.models import (
    ActionReference,
    BranchProtection,
    ContainerImage,
    PipelineModel,
    PipelinePermissions,
    PipelineStage,
    PipelineStep,
    PlatformType,
)


@pytest.fixture
def default_config() -> SpektciConfig:
    """A default SpektciConfig with all defaults."""
    return SpektciConfig()


@pytest.fixture
def sample_pipeline() -> PipelineModel:
    """A sample PipelineModel with various elements for testing."""
    return PipelineModel(
        platform=PlatformType.GITHUB,
        project="test-org/test-repo",
        branch="main",
        source_files=[".github/workflows/ci.yml"],
        stages=[
            PipelineStage(
                name="build",
                steps=[
                    PipelineStep(
                        name="Checkout",
                        action=ActionReference(
                            full_ref="actions/checkout@v4",
                            owner="actions",
                            name="checkout",
                            version="v4",
                            source_file=".github/workflows/ci.yml",
                        ),
                        source_file=".github/workflows/ci.yml",
                    ),
                    PipelineStep(
                        name="Build",
                        script="make build",
                        source_file=".github/workflows/ci.yml",
                    ),
                ],
            ),
            PipelineStage(
                name="test",
                steps=[
                    PipelineStep(
                        name="Run tests",
                        script="make test",
                        source_file=".github/workflows/ci.yml",
                    ),
                ],
            ),
        ],
        images=[
            ContainerImage(
                full_ref="python:3.11-slim",
                repository="python",
                tag="3.11-slim",
                source_file=".github/workflows/ci.yml",
                is_docker_official=True,
            ),
        ],
        actions=[
            ActionReference(
                full_ref="actions/checkout@v4",
                owner="actions",
                name="checkout",
                version="v4",
                source_file=".github/workflows/ci.yml",
            ),
        ],
        permissions=PipelinePermissions(
            top_level={"contents": "read"},
        ),
        raw_content={
            ".github/workflows/ci.yml": "name: CI\non: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n",
        },
    )


@pytest.fixture
def pipeline_with_issues() -> PipelineModel:
    """A pipeline model with various compliance issues."""
    return PipelineModel(
        platform=PlatformType.GITHUB,
        project="test-org/test-repo",
        branch="main",
        source_files=[".github/workflows/deploy.yml"],
        stages=[
            PipelineStage(
                name="deploy",
                steps=[
                    PipelineStep(
                        name="Deploy",
                        action=ActionReference(
                            full_ref="actions/checkout@main",
                            owner="actions",
                            name="checkout",
                            version="main",
                            source_file=".github/workflows/deploy.yml",
                        ),
                        source_file=".github/workflows/deploy.yml",
                    ),
                ],
            ),
        ],
        images=[
            ContainerImage(
                full_ref="random/tool:latest",
                registry="docker.io",
                repository="random/tool",
                tag="latest",
                source_file=".github/workflows/deploy.yml",
            ),
            ContainerImage(
                full_ref="evil-registry.com/malware:dev",
                registry="evil-registry.com",
                repository="malware",
                tag="dev",
                source_file=".github/workflows/deploy.yml",
            ),
        ],
        actions=[
            ActionReference(
                full_ref="actions/checkout@main",
                owner="actions",
                name="checkout",
                version="main",
                source_file=".github/workflows/deploy.yml",
            ),
        ],
        branch_protections=[
            BranchProtection(
                branch="main",
                is_protected=False,
            ),
        ],
        permissions=PipelinePermissions(
            top_level="write-all",
        ),
        raw_content={
            ".github/workflows/deploy.yml": (
                'name: Deploy\n'
                'on: push\n'
                'jobs:\n'
                '  deploy:\n'
                '    runs-on: ubuntu-latest\n'
                '    env:\n'
                '      SECRET_KEY: "supersecretpassword123"\n'
                '      API_TOKEN: "ghp_abcdefghijklmnopqrstuvwxyz1234567890"\n'
            ),
        },
    )
