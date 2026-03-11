"""C008 — Pipeline dependencies must be up to date."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from spektci.controls.base import BaseControl
from spektci.core.result import ControlResult, ControlStatus, Finding, Severity

if TYPE_CHECKING:
    from spektci.config.schema import SpektciConfig
    from spektci.core.models import PipelineModel

SEMVER_PATTERN = re.compile(r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?$")


class OutdatedDepsControl(BaseControl):
    """C008: Check if referenced actions, orbs, or plugins have newer versions.

    Note: Full version-checking requires API calls to the respective package
    registries. This control currently checks for version format and flags
    obviously outdated references (e.g., v1 when v3 exists). Full version
    resolution is planned for a future release.
    """

    @property
    def control_id(self) -> str:
        return "C008"

    @property
    def name(self) -> str:
        return "Pipeline dependencies must be up to date"

    def evaluate(self, pipeline: PipelineModel, config: SpektciConfig) -> ControlResult:
        cfg = config.controls.outdated_deps
        findings: list[Finding] = []

        # Group actions by name and find the latest version used
        action_versions: dict[str, list[tuple[str, str, str, int]]] = {}
        for action in pipeline.actions:
            key = f"{action.owner}/{action.name}" if action.owner else action.name
            action_versions.setdefault(key, []).append(
                (action.version, action.full_ref, action.source_file, action.source_line)
            )

        # Check version metadata if available in pipeline metadata
        latest_versions: dict[str, str] = {}
        if "latest_action_versions" in pipeline.metadata:
            raw = pipeline.metadata["latest_action_versions"]
            if isinstance(raw, dict):
                latest_versions = {k: str(v) for k, v in raw.items()}

        for action_name, versions in action_versions.items():
            latest = latest_versions.get(action_name)
            if not latest:
                continue

            latest_parsed = self._parse_version(latest)
            if not latest_parsed:
                continue

            for version, full_ref, src_file, src_line in versions:
                current_parsed = self._parse_version(version)
                if not current_parsed:
                    continue

                major_diff = latest_parsed[0] - current_parsed[0]
                minor_diff = latest_parsed[1] - current_parsed[1]

                if major_diff > cfg.max_major_behind:
                    findings.append(
                        Finding(
                            control_id=self.control_id,
                            control_name=self.name,
                            severity=Severity.WARNING,
                            message=(
                                f"Action '{full_ref}' is {major_diff} major version(s) "
                                f"behind (latest: {latest})"
                            ),
                            source_file=src_file,
                            source_line=src_line,
                            remediation=f"Update '{action_name}' to {latest}.",
                        )
                    )
                elif major_diff == 0 and minor_diff > cfg.max_minor_behind:
                    findings.append(
                        Finding(
                            control_id=self.control_id,
                            control_name=self.name,
                            severity=Severity.INFO,
                            message=(
                                f"Action '{full_ref}' is {minor_diff} minor version(s) "
                                f"behind (latest: {latest})"
                            ),
                            source_file=src_file,
                            source_line=src_line,
                            remediation=f"Consider updating '{action_name}' to {latest}.",
                        )
                    )

        return ControlResult(
            control_id=self.control_id,
            control_name=self.name,
            status=ControlStatus.FAIL if findings else ControlStatus.PASS,
            findings=findings,
        )

    @staticmethod
    def _parse_version(version: str) -> tuple[int, int, int] | None:
        """Parse a semver-like version string into (major, minor, patch)."""
        match = SEMVER_PATTERN.match(version)
        if not match:
            return None
        return (
            int(match.group(1)),
            int(match.group(2) or 0),
            int(match.group(3) or 0),
        )
