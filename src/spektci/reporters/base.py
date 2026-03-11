"""BaseReporter — abstract base class for output formatters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from spektci.config.schema import SpektciConfig
    from spektci.core.result import AnalysisResult


class BaseReporter(ABC):
    """Abstract base class for all report formatters."""

    @abstractmethod
    def render(self, result: AnalysisResult, config: SpektciConfig) -> str:
        """Render the analysis result as a formatted string.

        Args:
            result: The analysis result to render.
            config: The configuration used for the analysis.

        Returns:
            Formatted report as a string.
        """
