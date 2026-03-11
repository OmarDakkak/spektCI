"""Azure DevOps adapter — stub implementation (planned for v0.4)."""

from __future__ import annotations

from spektci.adapters.base import BasePlatformAdapter, RawPipelineData
from spektci.config.schema import SpektciConfig
from spektci.core.models import BranchProtection, PipelineModel, PlatformType


class AzureDevOpsAdapter(BasePlatformAdapter):
    """Platform adapter for Azure DevOps (stub — planned for v0.4)."""

    def detect(self, remote_url: str) -> bool:
        return "dev.azure.com" in remote_url or "visualstudio.com" in remote_url

    def collect(self, config: SpektciConfig) -> RawPipelineData:
        raise NotImplementedError(
            "Azure DevOps adapter is planned for v0.4. "
            "See https://github.com/spektci/spektci/issues for updates."
        )

    def parse(self, raw: RawPipelineData) -> PipelineModel:
        return PipelineModel(platform=PlatformType.AZURE)

    def get_branch_protection(self, branch: str) -> BranchProtection:
        return BranchProtection(branch=branch, is_protected=False)
