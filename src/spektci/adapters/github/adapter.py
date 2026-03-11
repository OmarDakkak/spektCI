"""GitHub Actions adapter — orchestrates collection and parsing."""

from __future__ import annotations

import logging

from spektci.adapters.base import BasePlatformAdapter, RawPipelineData
from spektci.adapters.detector import get_repo_from_remote
from spektci.adapters.github.collector import GitHubCollector
from spektci.adapters.github.parser import GitHubParser
from spektci.config.schema import SpektciConfig
from spektci.core.models import BranchProtection, PipelineModel

logger = logging.getLogger(__name__)


class GitHubAdapter(BasePlatformAdapter):
    """Platform adapter for GitHub Actions."""

    def __init__(self, config: SpektciConfig) -> None:
        super().__init__(config)
        self.collector = GitHubCollector(config)
        self.parser = GitHubParser()

    def detect(self, remote_url: str) -> bool:
        """Return True if the remote URL points to GitHub."""
        return "github.com" in remote_url

    def collect(self, config: SpektciConfig) -> RawPipelineData:
        """Fetch workflow files and repo settings from GitHub API."""
        repo = config.platform.project or get_repo_from_remote()
        if not repo:
            raise ValueError(
                "Could not determine repository. "
                "Use --repo owner/repo to specify it."
            )

        logger.info("Collecting GitHub Actions data for %s", repo)
        return self.collector.collect(repo)

    def parse(self, raw: RawPipelineData) -> PipelineModel:
        """Parse raw GitHub data into PipelineModel."""
        return self.parser.parse(raw)

    def get_branch_protection(self, branch: str) -> BranchProtection:
        """Fetch branch protection rules from GitHub API."""
        repo = self.config.platform.project or get_repo_from_remote()
        if not repo:
            raise ValueError("Could not determine repository for branch protection check.")

        return self.collector.get_branch_protection(repo, branch)
