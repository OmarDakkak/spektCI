"""BasePlatformAdapter — abstract base class for platform adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from spektci.config.schema import SpektciConfig
    from spektci.core.models import BranchProtection, PipelineModel


@dataclass
class RawPipelineData:
    """Raw data collected from a CI/CD platform before parsing.

    This is the intermediate format between collection and parsing.
    Each adapter defines what goes in here.
    """

    config_files: dict[str, str] = field(default_factory=dict)
    """Mapping of filename → file content for pipeline config files."""

    api_data: dict[str, Any] = field(default_factory=dict)
    """Data fetched from platform APIs (repo info, branch protection, etc.)."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional platform-specific metadata."""


class BasePlatformAdapter(ABC):
    """Base class for all platform adapters.

    Each CI/CD platform has a dedicated adapter that handles:
    - API communication
    - Config file discovery and reading
    - Data normalization into PipelineModel
    """

    def __init__(self, config: SpektciConfig) -> None:
        self.config = config

    @abstractmethod
    def detect(self, remote_url: str) -> bool:
        """Return True if this adapter handles the given git remote URL."""

    @abstractmethod
    def collect(self, config: SpektciConfig) -> RawPipelineData:
        """Fetch pipeline config and repo settings from API or local files.

        Args:
            config: The spektci configuration.

        Returns:
            Raw pipeline data for parsing.
        """

    @abstractmethod
    def parse(self, raw: RawPipelineData) -> PipelineModel:
        """Normalize raw data into the common PipelineModel IR.

        Args:
            raw: Raw data from the collect step.

        Returns:
            A normalized PipelineModel.
        """

    @abstractmethod
    def get_branch_protection(self, branch: str) -> BranchProtection:
        """Fetch branch protection rules for the given branch.

        Args:
            branch: Branch name to check.

        Returns:
            BranchProtection settings for the branch.
        """
