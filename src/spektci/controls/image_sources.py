"""C002 — Container images must come from authorized sources."""

from __future__ import annotations

import fnmatch
from typing import TYPE_CHECKING

from spektci.controls.base import BaseControl
from spektci.core.result import ControlResult, ControlStatus, Finding, Severity

if TYPE_CHECKING:
    from spektci.config.schema import SpektciConfig
    from spektci.core.models import PipelineModel


class ImageSourcesControl(BaseControl):
    """C002: Ensure container images come from trusted registries only."""

    @property
    def control_id(self) -> str:
        return "C002"

    @property
    def name(self) -> str:
        return "Container images must come from authorized sources"

    def evaluate(self, pipeline: PipelineModel, config: SpektciConfig) -> ControlResult:
        cfg = config.controls.image_sources
        trusted_patterns = list(cfg.trusted_registries)
        findings: list[Finding] = []

        for image in pipeline.images:
            if self._is_trusted(
                image.registry,
                image.is_docker_official,
                cfg.trust_docker_official,
                trusted_patterns,
            ):
                continue

            findings.append(
                Finding(
                    control_id=self.control_id,
                    control_name=self.name,
                    severity=Severity.ERROR,
                    message=(
                        f"Image '{image.full_ref}' comes from unauthorized "
                        f"registry '{image.registry or 'unknown'}'"
                    ),
                    source_file=image.source_file,
                    source_line=image.source_line,
                    remediation=(
                        "Use an image from a trusted registry or add this registry to "
                        "'controls.image_sources.trusted_registries' in .spektci.yaml."
                    ),
                )
            )

        return ControlResult(
            control_id=self.control_id,
            control_name=self.name,
            status=ControlStatus.FAIL if findings else ControlStatus.PASS,
            findings=findings,
        )

    @staticmethod
    def _is_trusted(
        registry: str | None,
        is_docker_official: bool,
        trust_official: bool,
        trusted_patterns: list[str],
    ) -> bool:
        """Check whether an image registry is trusted."""
        if trust_official and is_docker_official:
            return True

        if not registry:
            # No registry specified — depends on trust_docker_official
            return trust_official

        for pattern in trusted_patterns:
            if fnmatch.fnmatch(registry, pattern) or fnmatch.fnmatch(f"{registry}/", pattern):
                return True

        return False
