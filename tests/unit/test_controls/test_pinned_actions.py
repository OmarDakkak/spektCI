"""Tests for C005 — Pinned actions control."""

from __future__ import annotations

from spektci.config.schema import SpektciConfig
from spektci.controls.pinned_actions import PinnedActionsControl
from spektci.core.models import ActionReference, PipelineModel, PlatformType
from spektci.core.result import ControlStatus


def _make_pipeline(actions: list[ActionReference]) -> PipelineModel:
    return PipelineModel(
        platform=PlatformType.GITHUB,
        project="test/repo",
        branch="main",
        actions=actions,
    )


class TestPinnedActionsControl:
    """Tests for C005."""

    def setup_method(self) -> None:
        self.control = PinnedActionsControl()
        self.config = SpektciConfig()

    def test_passes_with_tagged_actions(self) -> None:
        pipeline = _make_pipeline(
            [
                ActionReference(
                    full_ref="actions/checkout@v4",
                    owner="actions",
                    name="checkout",
                    version="v4",
                ),
            ]
        )
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.PASS

    def test_fails_on_main_ref(self) -> None:
        pipeline = _make_pipeline(
            [
                ActionReference(
                    full_ref="actions/checkout@main",
                    owner="actions",
                    name="checkout",
                    version="main",
                ),
            ]
        )
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.FAIL
        assert result.finding_count == 1

    def test_fails_on_latest_ref(self) -> None:
        pipeline = _make_pipeline(
            [
                ActionReference(
                    full_ref="some/action@latest",
                    owner="some",
                    name="action",
                    version="latest",
                ),
            ]
        )
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.FAIL

    def test_sha_pinning_required(self) -> None:
        config = SpektciConfig()
        config.controls.pinned_actions.require_sha_pinning = True
        pipeline = _make_pipeline(
            [
                ActionReference(
                    full_ref="actions/checkout@v4",
                    owner="actions",
                    name="checkout",
                    version="v4",
                    is_sha_pinned=False,
                ),
            ]
        )
        result = self.control.evaluate(pipeline, config)
        assert result.status == ControlStatus.FAIL  # Not SHA-pinned

    def test_sha_pinned_passes(self) -> None:
        config = SpektciConfig()
        config.controls.pinned_actions.require_sha_pinning = True
        pipeline = _make_pipeline(
            [
                ActionReference(
                    full_ref="actions/checkout@a81bbbf8298c0fa03ea29cdc473d45769f953675",
                    owner="actions",
                    name="checkout",
                    version="a81bbbf8298c0fa03ea29cdc473d45769f953675",
                    is_sha_pinned=True,
                ),
            ]
        )
        result = self.control.evaluate(pipeline, config)
        assert result.status == ControlStatus.PASS
