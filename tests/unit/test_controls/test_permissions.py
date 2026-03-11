"""Tests for C007 — Permissions control."""

from __future__ import annotations

from spektci.config.schema import SpektciConfig
from spektci.controls.permissions import PermissionsControl
from spektci.core.models import PipelineModel, PipelinePermissions, PlatformType
from spektci.core.result import ControlStatus


class TestPermissionsControl:
    """Tests for C007."""

    def setup_method(self) -> None:
        self.control = PermissionsControl()
        self.config = SpektciConfig()

    def test_passes_with_read_permissions(self) -> None:
        pipeline = PipelineModel(
            platform=PlatformType.GITHUB,
            project="test/repo",
            branch="main",
            permissions=PipelinePermissions(
                top_level={"contents": "read", "packages": "read"},
            ),
        )
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.PASS

    def test_fails_on_write_all(self) -> None:
        pipeline = PipelineModel(
            platform=PlatformType.GITHUB,
            project="test/repo",
            branch="main",
            permissions=PipelinePermissions(top_level="write-all"),
        )
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.FAIL

    def test_fails_on_privileged_container(self) -> None:
        pipeline = PipelineModel(
            platform=PlatformType.GITHUB,
            project="test/repo",
            branch="main",
            permissions=PipelinePermissions(has_privileged_containers=True),
        )
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.FAIL

    def test_warns_on_write_scope(self) -> None:
        pipeline = PipelineModel(
            platform=PlatformType.GITHUB,
            project="test/repo",
            branch="main",
            permissions=PipelinePermissions(
                top_level={"contents": "read", "packages": "write"},
            ),
        )
        result = self.control.evaluate(pipeline, self.config)
        assert result.finding_count >= 1
