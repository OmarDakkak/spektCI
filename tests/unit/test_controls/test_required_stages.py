"""Tests for C006 — Required stages control."""

from __future__ import annotations

from spektci.config.schema import SpektciConfig
from spektci.controls.required_stages import RequiredStagesControl
from spektci.core.models import (
    ActionReference,
    PipelineModel,
    PipelineStage,
    PipelineStep,
    PlatformType,
)
from spektci.core.result import ControlStatus


class TestRequiredStagesControl:
    """Tests for C006."""

    def setup_method(self) -> None:
        self.control = RequiredStagesControl()
        self.config = SpektciConfig()

    def test_passes_with_all_required_stages(self) -> None:
        pipeline = PipelineModel(
            platform=PlatformType.GITHUB,
            project="test/repo",
            branch="main",
            stages=[
                PipelineStage(
                    name="sast",
                    steps=[
                        PipelineStep(
                            name="Run CodeQL",
                            action=ActionReference(
                                full_ref="github/codeql-action/analyze@v3",
                                name="codeql-action",
                            ),
                        ),
                    ],
                ),
                PipelineStage(
                    name="secret_scanning",
                    steps=[
                        PipelineStep(
                            name="Run gitleaks",
                            action=ActionReference(
                                full_ref="gitleaks/gitleaks-action@v2",
                                name="gitleaks-action",
                            ),
                        ),
                    ],
                ),
            ],
        )
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.PASS

    def test_fails_when_missing_sast(self) -> None:
        pipeline = PipelineModel(
            platform=PlatformType.GITHUB,
            project="test/repo",
            branch="main",
            stages=[
                PipelineStage(
                    name="secret_scanning",
                    steps=[
                        PipelineStep(name="gitleaks", script="gitleaks detect"),
                    ],
                ),
            ],
        )
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.FAIL
        assert any("sast" in f.message for f in result.findings)

    def test_fails_when_no_stages(self) -> None:
        pipeline = PipelineModel(
            platform=PlatformType.GITHUB,
            project="test/repo",
            branch="main",
            stages=[],
        )
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.FAIL
