"""Tests for C001 — Image tags control."""

from __future__ import annotations

from spektci.config.schema import SpektciConfig
from spektci.controls.image_tags import ImageTagsControl
from spektci.core.models import ContainerImage, PipelineModel, PlatformType
from spektci.core.result import ControlStatus


def _make_pipeline(images: list[ContainerImage]) -> PipelineModel:
    return PipelineModel(
        platform=PlatformType.GITHUB,
        project="test/repo",
        branch="main",
        images=images,
    )


class TestImageTagsControl:
    """Tests for C001."""

    def setup_method(self) -> None:
        self.control = ImageTagsControl()
        self.config = SpektciConfig()

    def test_passes_with_pinned_tags(self) -> None:
        pipeline = _make_pipeline([
            ContainerImage(full_ref="python:3.11-slim", tag="3.11-slim"),
            ContainerImage(full_ref="node:20-alpine", tag="20-alpine"),
        ])
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.PASS
        assert result.finding_count == 0

    def test_fails_on_latest_tag(self) -> None:
        pipeline = _make_pipeline([
            ContainerImage(full_ref="python:latest", tag="latest"),
        ])
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.FAIL
        assert result.finding_count == 1
        assert "latest" in result.findings[0].message

    def test_fails_on_dev_tag(self) -> None:
        pipeline = _make_pipeline([
            ContainerImage(full_ref="myapp:dev", tag="dev"),
        ])
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.FAIL
        assert result.finding_count == 1

    def test_fails_on_multiple_forbidden_tags(self) -> None:
        pipeline = _make_pipeline([
            ContainerImage(full_ref="app:latest", tag="latest"),
            ContainerImage(full_ref="db:staging", tag="staging"),
            ContainerImage(full_ref="cache:dev", tag="dev"),
        ])
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.FAIL
        assert result.finding_count == 3

    def test_passes_with_no_images(self) -> None:
        pipeline = _make_pipeline([])
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.PASS

    def test_digest_image_passes(self) -> None:
        pipeline = _make_pipeline([
            ContainerImage(
                full_ref="python@sha256:abc123",
                tag=None,
                digest="sha256:abc123",
            ),
        ])
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.PASS
