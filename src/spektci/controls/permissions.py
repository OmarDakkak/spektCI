"""C007 — Permissions must follow least-privilege."""

from __future__ import annotations

from typing import TYPE_CHECKING

from spektci.controls.base import BaseControl
from spektci.core.result import ControlResult, ControlStatus, Finding, Severity

if TYPE_CHECKING:
    from spektci.config.schema import SpektciConfig
    from spektci.core.models import PipelineModel

# Permission levels ordered from least to most permissive
PERMISSION_LEVELS = {"none": 0, "read": 1, "write": 2, "admin": 3}

OVERLY_PERMISSIVE_VALUES = {"write-all", "write", "admin"}


class PermissionsControl(BaseControl):
    """C007: Detect overly permissive workflow/pipeline permissions."""

    @property
    def control_id(self) -> str:
        return "C007"

    @property
    def name(self) -> str:
        return "Permissions must follow least-privilege"

    def evaluate(self, pipeline: PipelineModel, config: SpektciConfig) -> ControlResult:
        cfg = config.controls.permissions
        findings: list[Finding] = []
        max_level = PERMISSION_LEVELS.get(cfg.max_github_permissions, 1)

        perms = pipeline.permissions

        # Check top-level permissions
        if isinstance(perms.top_level, str):
            perm_str = perms.top_level.lower().replace("-", "").replace("_", "")
            # "write-all" or "writeall"
            if perm_str in {"writeall", "admin"}:
                findings.append(
                    Finding(
                        control_id=self.control_id,
                        control_name=self.name,
                        severity=Severity.ERROR,
                        message=(
                            f"Top-level permissions set to '{perms.top_level}' "
                            f"(exceeds max '{cfg.max_github_permissions}')"
                        ),
                        remediation=(
                            "Set top-level permissions to 'read-all' or define "
                            "per-scope permissions with least-privilege."
                        ),
                    )
                )
        elif isinstance(perms.top_level, dict):
            for scope, level in perms.top_level.items():
                level_val = PERMISSION_LEVELS.get(level, 0)
                if level_val > max_level:
                    findings.append(
                        Finding(
                            control_id=self.control_id,
                            control_name=self.name,
                            severity=Severity.WARNING,
                            message=(
                                f"Permission '{scope}: {level}' exceeds max "
                                f"'{cfg.max_github_permissions}'"
                            ),
                            remediation=(
                                f"Reduce '{scope}' permission to "
                                f"'{cfg.max_github_permissions}' or lower."
                            ),
                        )
                    )

        # Check privileged containers
        if cfg.flag_privileged_containers and perms.has_privileged_containers:
            findings.append(
                Finding(
                    control_id=self.control_id,
                    control_name=self.name,
                    severity=Severity.ERROR,
                    message="Pipeline uses privileged containers",
                    remediation=(
                        "Remove 'privileged: true' from container definitions. "
                        "Privileged containers have full host access."
                    ),
                )
            )

        # Check unrestricted network
        if cfg.flag_unrestricted_network and perms.has_unrestricted_network:
            findings.append(
                Finding(
                    control_id=self.control_id,
                    control_name=self.name,
                    severity=Severity.WARNING,
                    message="Pipeline has unrestricted network access in containers",
                    remediation="Restrict container network access where possible.",
                )
            )

        return ControlResult(
            control_id=self.control_id,
            control_name=self.name,
            status=ControlStatus.FAIL if findings else ControlStatus.PASS,
            findings=findings,
        )
