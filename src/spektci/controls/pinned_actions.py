"""C005 — Actions/orbs/plugins must use pinned versions."""

from __future__ import annotations

import re

from spektci.config.schema import SpektciConfig
from spektci.controls.base import BaseControl
from spektci.core.models import PipelineModel
from spektci.core.result import ControlResult, ControlStatus, Finding, Severity

SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class PinnedActionsControl(BaseControl):
    """C005: Prevent use of mutable version references on actions/orbs/pipes."""

    @property
    def control_id(self) -> str:
        return "C005"

    @property
    def name(self) -> str:
        return "Actions/orbs/plugins must use pinned versions"

    def evaluate(self, pipeline: PipelineModel, config: SpektciConfig) -> ControlResult:
        cfg = config.controls.pinned_actions
        forbidden = set(cfg.forbidden_refs)
        findings: list[Finding] = []

        for action in pipeline.actions:
            version = action.version

            # Check if using a forbidden ref (branch name, HEAD, etc.)
            if version in forbidden:
                findings.append(
                    Finding(
                        control_id=self.control_id,
                        control_name=self.name,
                        severity=Severity.ERROR,
                        message=(
                            f"Action '{action.full_ref}' uses forbidden mutable ref "
                            f"'{version}'"
                        ),
                        source_file=action.source_file,
                        source_line=action.source_line,
                        remediation=(
                            f"Pin '{action.full_ref}' to a specific version tag "
                            f"or commit SHA."
                        ),
                    )
                )
                continue

            # If SHA pinning is required, verify it
            if cfg.require_sha_pinning and not action.is_sha_pinned:
                findings.append(
                    Finding(
                        control_id=self.control_id,
                        control_name=self.name,
                        severity=Severity.WARNING,
                        message=(
                            f"Action '{action.full_ref}' is not pinned to a commit SHA"
                        ),
                        source_file=action.source_file,
                        source_line=action.source_line,
                        remediation=(
                            f"Pin '{action.owner}/{action.name}' to a full commit SHA "
                            f"(40 hex characters) for maximum reproducibility."
                        ),
                    )
                )

            # Check for empty or no version
            if not version:
                findings.append(
                    Finding(
                        control_id=self.control_id,
                        control_name=self.name,
                        severity=Severity.WARNING,
                        message=(
                            f"Action '{action.full_ref}' has no version specified"
                        ),
                        source_file=action.source_file,
                        source_line=action.source_line,
                        remediation="Always specify a version for external actions.",
                    )
                )

        return ControlResult(
            control_id=self.control_id,
            control_name=self.name,
            status=ControlStatus.FAIL if findings else ControlStatus.PASS,
            findings=findings,
        )
