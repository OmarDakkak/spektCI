"""End-to-end integration tests for spektci."""

from __future__ import annotations

import pytest

from spektci.config.schema import SpektciConfig
from spektci.controls.registry import get_enabled_controls
from spektci.core.engine import AnalysisEngine


@pytest.mark.integration
class TestEndToEnd:
    """Integration tests that require API access or full pipeline runs."""

    def test_all_controls_can_be_instantiated(self) -> None:
        """Verify that all controls can be created and have valid IDs."""
        config = SpektciConfig()
        controls = get_enabled_controls(config)
        assert len(controls) == 8
        ids = {c.control_id for c in controls}
        expected = {"C001", "C002", "C003", "C004", "C005", "C006", "C007", "C008"}
        assert ids == expected

    def test_engine_runs_with_sample_pipeline(
        self, sample_pipeline: object, default_config: object
    ) -> None:
        """Run the engine against a sample pipeline (mocked adapter)."""
        from unittest.mock import MagicMock

        from spektci.core.models import BranchProtection

        config = default_config  # type: ignore[assignment]
        pipeline = sample_pipeline

        adapter = MagicMock()
        adapter.collect.return_value = MagicMock()
        adapter.parse.return_value = pipeline
        adapter.get_branch_protection.return_value = BranchProtection(
            branch="main", is_protected=True, require_pr_review=True,
            min_approvals=1, require_status_checks=True, block_force_push=True,
        )

        controls = get_enabled_controls(config)  # type: ignore[arg-type]
        engine = AnalysisEngine(adapter=adapter, controls=controls, config=config)  # type: ignore[arg-type]
        result = engine.run()

        assert result.platform == "github"
        assert result.total_controls == 8
        assert 0 <= result.compliance_score <= 100
