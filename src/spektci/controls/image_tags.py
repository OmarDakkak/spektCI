"""C001 — Container images must not use forbidden tags."""

from __future__ import annotations

from spektci.config.schema import SpektciConfig
from spektci.controls.base import BaseControl
from spektci.core.models import PipelineModel
from spektci.core.result import ControlResult, ControlStatus, Finding, Severity


class ImageTagsControl(BaseControl):
    """C001: Detect container images using forbidden mutable tags (e.g. latest, dev)."""

    @property
    def control_id(self) -> str:
        return "C001"

    @property
    def name(self) -> str:
        return "Container images must not use forbidden tags"

    def evaluate(self, pipeline: PipelineModel, config: SpektciConfig) -> ControlResult:
        cfg = config.controls.image_tags
        forbidden = set(cfg.forbidden_tags)
        findings: list[Finding] = []

        for image in pipeline.images:
            if image.tag and image.tag in forbidden:
                findings.append(
                    Finding(
                        control_id=self.control_id,
                        control_name=self.name,
                        severity=Severity.ERROR,
                        message=(
                            f"Image '{image.full_ref}' uses forbidden tag '{image.tag}'"
                        ),
                        source_file=image.source_file,
                        source_line=image.source_line,
                        remediation=(
                            f"Pin image to a specific immutable tag or digest instead of "
                            f"'{image.tag}'."
                        ),
                    )
                )

        return ControlResult(
            control_id=self.control_id,
            control_name=self.name,
            status=ControlStatus.FAIL if findings else ControlStatus.PASS,
            findings=findings,
        )
