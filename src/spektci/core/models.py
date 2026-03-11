"""Common intermediate representation for CI/CD pipeline configurations.

The PipelineModel is the platform-agnostic IR that all adapters normalize into.
Controls evaluate rules against this model, never against raw platform data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class PlatformType(StrEnum):
    """Supported CI/CD platforms."""

    GITHUB = "github"
    JENKINS = "jenkins"
    BITBUCKET = "bitbucket"
    AZURE = "azure"
    CIRCLECI = "circleci"


@dataclass
class ContainerImage:
    """A container image reference found in a pipeline definition."""

    full_ref: str
    """Full image reference, e.g. 'docker.io/library/python:3.11-slim'."""

    registry: str | None = None
    """Registry hostname, e.g. 'docker.io', 'ghcr.io'."""

    repository: str = ""
    """Image repository, e.g. 'library/python'."""

    tag: str | None = None
    """Image tag, e.g. '3.11-slim'. None if using digest."""

    digest: str | None = None
    """Image digest, e.g. 'sha256:abc...'."""

    source_file: str = ""
    """File where this image reference was found."""

    source_line: int = 0
    """Line number in the source file."""

    is_docker_official: bool = False
    """True if this is an official Docker Hub image (library/*)."""


@dataclass
class ActionReference:
    """A reference to an external action, orb, pipe, task, or plugin."""

    full_ref: str
    """Full reference string, e.g. 'actions/checkout@v4'."""

    owner: str = ""
    """Owner/org of the action."""

    name: str = ""
    """Action/orb/pipe name."""

    version: str = ""
    """Version reference (tag, branch, or SHA)."""

    is_sha_pinned: bool = False
    """True if pinned to a commit SHA."""

    source_file: str = ""
    """File where this reference was found."""

    source_line: int = 0
    """Line number in the source file."""


@dataclass
class PipelineStage:
    """A stage/job in the pipeline."""

    name: str
    """Stage or job name."""

    steps: list[PipelineStep] = field(default_factory=list)
    """Steps within this stage."""

    images: list[ContainerImage] = field(default_factory=list)
    """Container images used in this stage."""

    environment: dict[str, str] = field(default_factory=dict)
    """Environment variables defined at the stage level."""


@dataclass
class PipelineStep:
    """A single step within a stage/job."""

    name: str = ""
    """Step name or display name."""

    action: ActionReference | None = None
    """External action/task reference, if applicable."""

    script: str = ""
    """Inline script content, if applicable."""

    environment: dict[str, str] = field(default_factory=dict)
    """Environment variables defined at the step level."""

    source_file: str = ""
    """File where this step was found."""

    source_line: int = 0
    """Line number."""


@dataclass
class BranchProtection:
    """Branch protection / policy settings retrieved from the platform API."""

    branch: str
    """Branch name."""

    is_protected: bool = False
    """Whether the branch has protection enabled."""

    require_pr_review: bool = False
    """Requires pull request reviews before merging."""

    min_approvals: int = 0
    """Minimum number of approvals required."""

    require_status_checks: bool = False
    """Requires status checks to pass before merging."""

    required_checks: list[str] = field(default_factory=list)
    """List of required status check names."""

    block_force_push: bool = False
    """Blocks force pushes to the branch."""

    block_deletions: bool = False
    """Blocks branch deletion."""


@dataclass
class PipelinePermissions:
    """Workflow/pipeline-level permission settings."""

    top_level: str | dict[str, str] | None = None
    """Top-level permissions declaration (e.g. 'read-all', or per-scope dict)."""

    job_level: dict[str, str | dict[str, str]] = field(default_factory=dict)
    """Per-job permission overrides."""

    has_privileged_containers: bool = False
    """Whether any container runs in privileged mode."""

    has_unrestricted_network: bool = False
    """Whether any container has unrestricted network access."""


@dataclass
class PipelineModel:
    """Platform-agnostic intermediate representation of a CI/CD pipeline.

    This is the canonical data structure that all platform adapters produce
    and all compliance controls evaluate against.
    """

    platform: PlatformType
    """Which CI/CD platform this pipeline belongs to."""

    project: str = ""
    """Project identifier (e.g., 'owner/repo')."""

    branch: str = ""
    """Branch being analyzed."""

    source_files: list[str] = field(default_factory=list)
    """List of pipeline config files that were parsed."""

    stages: list[PipelineStage] = field(default_factory=list)
    """All stages/jobs in the pipeline."""

    images: list[ContainerImage] = field(default_factory=list)
    """All container images referenced across the pipeline."""

    actions: list[ActionReference] = field(default_factory=list)
    """All external action/orb/pipe/task references."""

    branch_protections: list[BranchProtection] = field(default_factory=list)
    """Branch protection settings for monitored branches."""

    permissions: PipelinePermissions = field(default_factory=PipelinePermissions)
    """Pipeline permission settings."""

    raw_content: dict[str, str] = field(default_factory=dict)
    """Raw file contents, keyed by filename (for secret scanning, etc.)."""

    environment: dict[str, str] = field(default_factory=dict)
    """Global environment variables."""

    metadata: dict[str, object] = field(default_factory=dict)
    """Platform-specific metadata that doesn't fit the common model."""
