"""BaseControl abstract class — contract for all compliance controls."""

from __future__ import annotations

from abc import ABC, abstractmethod

from spektci.config.schema import SpektciConfig
from spektci.core.models import PipelineModel
from spektci.core.result import ControlResult


class BaseControl(ABC):
    """Abstract base class for all compliance controls.

    Every control must define:
    - ``control_id``: e.g. ``"C001"``
    - ``name``: Human-readable name
    - ``evaluate()``: Evaluate the pipeline model and return a ControlResult
    """

    @property
    @abstractmethod
    def control_id(self) -> str:
        """Unique control identifier (e.g. 'C001')."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable control name."""

    @abstractmethod
    def evaluate(self, pipeline: PipelineModel, config: SpektciConfig) -> ControlResult:
        """Evaluate the pipeline model against this control.

        Args:
            pipeline: The normalized PipelineModel to evaluate.
            config: The full spektci configuration for accessing control settings.

        Returns:
            A ControlResult with status and findings.
        """
