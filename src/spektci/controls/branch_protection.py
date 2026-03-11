"""C003 — Branches must be protected."""

from __future__ import annotations

from spektci.config.schema import SpektciConfig
from spektci.controls.base import BaseControl
from spektci.core.models import PipelineModel
from spektci.core.result import ControlResult, ControlStatus, Finding, Severity


class BranchProtectionControl(BaseControl):
    """C003: Verify that critical branches have proper protection settings."""

    @property
    def control_id(self) -> str:
        return "C003"

    @property
    def name(self) -> str:
        return "Branches must be protected"

    def evaluate(self, pipeline: PipelineModel, config: SpektciConfig) -> ControlResult:
        cfg = config.controls.branch_protection
        findings: list[Finding] = []

        for bp in pipeline.branch_protections:
            if not bp.is_protected:
                findings.append(
                    Finding(
                        control_id=self.control_id,
                        control_name=self.name,
                        severity=Severity.ERROR,
                        message=f"Branch '{bp.branch}' is not protected",
                        remediation=(
                            f"Enable branch protection for '{bp.branch}' in your "
                            f"platform settings."
                        ),
                    )
                )
                continue

            # Check specific protection settings
            if cfg.require_pr_review and not bp.require_pr_review:
                findings.append(
                    Finding(
                        control_id=self.control_id,
                        control_name=self.name,
                        severity=Severity.WARNING,
                        message=(
                            f"Branch '{bp.branch}' does not require PR reviews"
                        ),
                        remediation="Enable 'Require a pull request before merging'.",
                    )
                )

            if bp.min_approvals < cfg.min_approvals:
                findings.append(
                    Finding(
                        control_id=self.control_id,
                        control_name=self.name,
                        severity=Severity.WARNING,
                        message=(
                            f"Branch '{bp.branch}' requires {bp.min_approvals} approvals, "
                            f"but policy requires {cfg.min_approvals}"
                        ),
                        remediation=(
                            f"Set minimum approvals to at least {cfg.min_approvals}."
                        ),
                    )
                )

            if cfg.require_status_checks and not bp.require_status_checks:
                findings.append(
                    Finding(
                        control_id=self.control_id,
                        control_name=self.name,
                        severity=Severity.WARNING,
                        message=(
                            f"Branch '{bp.branch}' does not require status checks"
                        ),
                        remediation="Enable 'Require status checks to pass'.",
                    )
                )

            if cfg.block_force_push and not bp.block_force_push:
                findings.append(
                    Finding(
                        control_id=self.control_id,
                        control_name=self.name,
                        severity=Severity.WARNING,
                        message=f"Branch '{bp.branch}' allows force pushes",
                        remediation="Enable 'Block force pushes'.",
                    )
                )

        # Check if all configured branches were found
        configured_branches = set(cfg.branches)
        found_branches = {bp.branch for bp in pipeline.branch_protections}
        missing = configured_branches - found_branches
        for branch_name in sorted(missing):
            # Skip glob patterns (those are informational)
            if "*" not in branch_name:
                findings.append(
                    Finding(
                        control_id=self.control_id,
                        control_name=self.name,
                        severity=Severity.INFO,
                        message=(
                            f"Branch protection for '{branch_name}' could not be verified"
                        ),
                        remediation="Ensure this branch exists and has protection enabled.",
                    )
                )

        has_errors = any(f.severity == Severity.ERROR for f in findings)
        return ControlResult(
            control_id=self.control_id,
            control_name=self.name,
            status=ControlStatus.FAIL if has_errors else ControlStatus.PASS,
            findings=findings,
        )
