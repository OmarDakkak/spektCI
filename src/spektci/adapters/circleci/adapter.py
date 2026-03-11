"""CircleCI adapter — stub implementation (planned for v0.5)."""

from __future__ import annotations

from spektci.adapters.base import BasePlatformAdapter, RawPipelineData
from spektci.config.schema import SpektciConfig
from spektci.core.models import BranchProtection, PipelineModel, PlatformType


class CircleCIAdapter(BasePlatformAdapter):
    """Platform adapter for CircleCI (stub — planned for v0.5)."""

    def detect(self, remote_url: str) -> bool:
        return False  # CircleCI doesn't have its own git hosting

    def collect(self, config: SpektciConfig) -> RawPipelineData:
        raise NotImplementedError(
            "CircleCI adapter is planned for v0.5. "
            "See https://github.com/spektci/spektci/issues for updates."
        )

    def parse(self, raw: RawPipelineData) -> PipelineModel:
        return PipelineModel(platform=PlatformType.CIRCLECI)

    def get_branch_protection(self, branch: str) -> BranchProtection:
        return BranchProtection(branch=branch, is_protected=False)
