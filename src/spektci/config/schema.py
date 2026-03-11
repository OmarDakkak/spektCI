"""Pydantic v2 models for the .spektci.yaml configuration file."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ── Control-specific config models ───────────────────────────────


class ImageTagsConfig(BaseModel):
    """C001 — Forbidden container image tags."""

    enabled: bool = True
    forbidden_tags: list[str] = Field(
        default_factory=lambda: ["latest", "dev", "main", "master", "staging"]
    )


class ImageSourcesConfig(BaseModel):
    """C002 — Authorized image registries."""

    enabled: bool = True
    trust_docker_official: bool = True
    trusted_registries: list[str] = Field(default_factory=list)


class BranchProtectionConfig(BaseModel):
    """C003 — Branch protection policies."""

    enabled: bool = True
    branches: list[str] = Field(
        default_factory=lambda: ["main", "master", "release/*", "production"]
    )
    require_pr_review: bool = True
    min_approvals: int = 1
    require_status_checks: bool = True
    block_force_push: bool = True


class HardcodedSecretsConfig(BaseModel):
    """C004 — Secrets in pipeline config."""

    enabled: bool = True
    patterns: list[str] = Field(default_factory=list)
    exclude_paths: list[str] = Field(default_factory=list)


class PinnedActionsConfig(BaseModel):
    """C005 — Mutable refs on actions/orbs/pipes."""

    enabled: bool = True
    require_sha_pinning: bool = False
    forbidden_refs: list[str] = Field(
        default_factory=lambda: ["main", "master", "HEAD", "latest"]
    )


class RequiredStagesConfig(BaseModel):
    """C006 — Required security stages."""

    enabled: bool = True
    require_all: list[str] = Field(default_factory=lambda: ["sast", "secret_scanning"])
    require_any: list[str] = Field(default_factory=list)


class PermissionsConfig(BaseModel):
    """C007 — Overly permissive permissions."""

    enabled: bool = True
    max_github_permissions: str = "read"
    flag_privileged_containers: bool = True
    flag_unrestricted_network: bool = True


class OutdatedDepsConfig(BaseModel):
    """C008 — Outdated pipeline dependencies."""

    enabled: bool = True
    max_major_behind: int = 1
    max_minor_behind: int = 3


# ── Aggregate controls config ───────────────────────────────────


class ControlsConfig(BaseModel):
    """All compliance control configurations."""

    image_tags: ImageTagsConfig = Field(default_factory=ImageTagsConfig)
    image_sources: ImageSourcesConfig = Field(default_factory=ImageSourcesConfig)
    branch_protection: BranchProtectionConfig = Field(default_factory=BranchProtectionConfig)
    hardcoded_secrets: HardcodedSecretsConfig = Field(default_factory=HardcodedSecretsConfig)
    pinned_actions: PinnedActionsConfig = Field(default_factory=PinnedActionsConfig)
    required_stages: RequiredStagesConfig = Field(default_factory=RequiredStagesConfig)
    permissions: PermissionsConfig = Field(default_factory=PermissionsConfig)
    outdated_deps: OutdatedDepsConfig = Field(default_factory=OutdatedDepsConfig)


# ── Top-level config sections ───────────────────────────────────


class GlobalConfig(BaseModel):
    """Global analysis settings."""

    threshold: int = Field(default=80, ge=0, le=100)
    fail_on: Literal["error", "warning", "info"] = "error"
    output_format: Literal["terminal", "json", "sarif"] = "terminal"
    output_file: str | None = None


class PlatformConfig(BaseModel):
    """Platform detection & override settings."""

    type: Literal["auto", "github", "jenkins", "bitbucket", "azure", "circleci"] = "auto"
    api_url: str | None = None
    project: str | None = None
    branch: str | None = None


# ── Root config model ────────────────────────────────────────────


class SpektciConfig(BaseModel):
    """Root configuration model for .spektci.yaml."""

    version: str = "1"
    global_: GlobalConfig = Field(default_factory=GlobalConfig, alias="global")
    platform: PlatformConfig = Field(default_factory=PlatformConfig)
    controls: ControlsConfig = Field(default_factory=ControlsConfig)

    model_config = {"populate_by_name": True}
