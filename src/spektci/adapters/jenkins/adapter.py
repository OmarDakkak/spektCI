"""Jenkins adapter — stub implementation (planned for v0.2)."""

from __future__ import annotations

from spektci.adapters.base import BasePlatformAdapter, RawPipelineData
from spektci.config.schema import SpektciConfig
from spektci.core.models import BranchProtection, PipelineModel, PlatformType


class JenkinsAdapter(BasePlatformAdapter):
    """Platform adapter for Jenkins (stub — planned for v0.2)."""

    def detect(self, remote_url: str) -> bool:
        return False

    def collect(self, config: SpektciConfig) -> RawPipelineData:
        raise NotImplementedError(
            "Jenkins adapter is planned for v0.2. "
            "See https://github.com/spektci/spektci/issues for updates."
        )

    def parse(self, raw: RawPipelineData) -> PipelineModel:
        return PipelineModel(platform=PlatformType.JENKINS)

    def get_branch_protection(self, branch: str) -> BranchProtection:
        return BranchProtection(branch=branch, is_protected=False)
