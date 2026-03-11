"""Analysis engine — orchestrates the full analysis pipeline."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from spektci.core.result import AnalysisResult, ControlResult, ControlStatus

if TYPE_CHECKING:
    from spektci.adapters.base import BasePlatformAdapter
    from spektci.config.schema import SpektciConfig
    from spektci.controls.base import BaseControl

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """Orchestrates the full compliance analysis pipeline.

    Flow:
        1. Adapter collects raw data (API + file reads)
        2. Adapter parses raw data → PipelineModel
        3. Controls evaluate rules against PipelineModel
        4. Results are aggregated into an AnalysisResult
    """

    def __init__(
        self,
        adapter: BasePlatformAdapter,
        controls: list[BaseControl],
        config: SpektciConfig,
    ) -> None:
        self.adapter = adapter
        self.controls = controls
        self.config = config

    def run(self) -> AnalysisResult:
        """Execute the full analysis and return results."""
        logger.info("Starting analysis with adapter: %s", self.adapter.__class__.__name__)

        # Step 1 & 2: Collect and parse
        logger.info("Collecting pipeline data...")
        raw_data = self.adapter.collect(self.config)
        logger.info("Parsing pipeline data into PipelineModel...")
        pipeline = self.adapter.parse(raw_data)

        # Fetch branch protections for configured branches
        bp_branches = self.config.controls.branch_protection.branches
        if self.config.controls.branch_protection.enabled and bp_branches:
            logger.info("Fetching branch protection for: %s", bp_branches)
            for branch_pattern in bp_branches:
                try:
                    bp = self.adapter.get_branch_protection(branch_pattern)
                    pipeline.branch_protections.append(bp)
                except Exception:
                    logger.warning("Could not fetch branch protection for %s", branch_pattern)

        # Step 3: Evaluate controls
        control_results: list[ControlResult] = []
        for control in self.controls:
            logger.info("Evaluating control: %s (%s)", control.control_id, control.name)
            try:
                result = control.evaluate(pipeline, self.config)
                control_results.append(result)
            except Exception as exc:
                logger.error("Control %s raised an error: %s", control.control_id, exc)
                control_results.append(
                    ControlResult(
                        control_id=control.control_id,
                        control_name=control.name,
                        status=ControlStatus.ERROR,
                        error_message=str(exc),
                    )
                )

        # Step 4: Aggregate
        result = AnalysisResult(
            platform=pipeline.platform.value,
            project=pipeline.project,
            branch=pipeline.branch,
            control_results=control_results,
        )

        logger.info(
            "Analysis complete: %.1f%% compliance (%d/%d controls passing)",
            result.compliance_score,
            result.passed_controls,
            result.total_controls,
        )
        return result
