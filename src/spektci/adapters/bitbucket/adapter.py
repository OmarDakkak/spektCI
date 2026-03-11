"""Bitbucket Pipelines adapter — stub implementation (planned for v0.3)."""

from __future__ import annotations

from spektci.adapters.base import BasePlatformAdapter, RawPipelineData
from spektci.config.schema import SpektciConfig
from spektci.core.models import BranchProtection, PipelineModel, PlatformType


class BitbucketAdapter(BasePlatformAdapter):
    """Platform adapter for Bitbucket Pipelines (stub — planned for v0.3)."""

    def detect(self, remote_url: str) -> bool:
        return "bitbucket.org" in remote_url

    def collect(self, config: SpektciConfig) -> RawPipelineData:
        raise NotImplementedError(
            "Bitbucket Pipelines adapter is planned for v0.3. "
            "See https://github.com/spektci/spektci/issues for updates."
        )

    def parse(self, raw: RawPipelineData) -> PipelineModel:
        return PipelineModel(platform=PlatformType.BITBUCKET)

    def get_branch_protection(self, branch: str) -> BranchProtection:
        return BranchProtection(branch=branch, is_protected=False)
