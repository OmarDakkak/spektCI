"""Tests for C002 — Image sources control."""

from __future__ import annotations

from spektci.config.schema import SpektciConfig
from spektci.controls.image_sources import ImageSourcesControl
from spektci.core.models import ContainerImage, PipelineModel, PlatformType
from spektci.core.result import ControlStatus


def _make_pipeline(images: list[ContainerImage]) -> PipelineModel:
    return PipelineModel(
        platform=PlatformType.GITHUB,
        project="test/repo",
        branch="main",
        images=images,
    )


class TestImageSourcesControl:
    """Tests for C002."""

    def setup_method(self) -> None:
        self.control = ImageSourcesControl()
        self.config = SpektciConfig()

    def test_passes_for_docker_official_images(self) -> None:
        pipeline = _make_pipeline([
            ContainerImage(
                full_ref="python:3.11",
                tag="3.11",
                is_docker_official=True,
            ),
        ])
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.PASS

    def test_fails_for_untrusted_registry(self) -> None:
        pipeline = _make_pipeline([
            ContainerImage(
                full_ref="evil.registry.com/malware:1.0",
                registry="evil.registry.com",
                tag="1.0",
                is_docker_official=False,
            ),
        ])
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.FAIL
        assert result.finding_count == 1

    def test_passes_for_trusted_registry(self) -> None:
        config = SpektciConfig()
        config.controls.image_sources.trusted_registries = ["ghcr.io/*"]
        pipeline = _make_pipeline([
            ContainerImage(
                full_ref="ghcr.io/myorg/myimage:1.0",
                registry="ghcr.io",
                tag="1.0",
                is_docker_official=False,
            ),
        ])
        result = self.control.evaluate(pipeline, config)
        assert result.status == ControlStatus.PASS

    def test_passes_with_no_images(self) -> None:
        pipeline = _make_pipeline([])
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.PASS
