"""C006 — Pipeline must include required security stages."""

from __future__ import annotations

from spektci.config.schema import SpektciConfig
from spektci.controls.base import BaseControl
from spektci.core.models import PipelineModel
from spektci.core.result import ControlResult, ControlStatus, Finding, Severity

# Keywords that indicate a stage/step is performing a certain security scan
STAGE_KEYWORDS: dict[str, list[str]] = {
    "sast": [
        "sast", "static-analysis", "static_analysis", "semgrep", "sonar",
        "codeql", "checkmarx", "fortify", "snyk-code", "bandit",
    ],
    "sca": [
        "sca", "dependency-check", "dependency_check", "dependabot",
        "snyk", "renovate", "npm-audit", "pip-audit", "safety",
    ],
    "secret_scanning": [
        "secret", "gitleaks", "trufflehog", "detect-secrets", "talisman",
        "git-secrets",
    ],
    "container_scanning": [
        "container-scan", "container_scan", "trivy", "grype", "anchore",
        "aqua", "twistlock", "prisma-cloud",
    ],
    "dast": [
        "dast", "dynamic-analysis", "dynamic_analysis", "zap", "burp",
    ],
}


class RequiredStagesControl(BaseControl):
    """C006: Ensure required security scanning stages are present in the pipeline."""

    @property
    def control_id(self) -> str:
        return "C006"

    @property
    def name(self) -> str:
        return "Pipeline must include required security stages"

    def evaluate(self, pipeline: PipelineModel, config: SpektciConfig) -> ControlResult:
        cfg = config.controls.required_stages
        findings: list[Finding] = []

        # Build a set of detected security stage types
        detected_types = self._detect_stage_types(pipeline)

        # Check require_all — every listed type must be present
        for required in cfg.require_all:
            if required not in detected_types:
                findings.append(
                    Finding(
                        control_id=self.control_id,
                        control_name=self.name,
                        severity=Severity.ERROR,
                        message=f"Missing required security stage: {required}",
                        remediation=(
                            f"Add a '{required}' stage to your pipeline. "
                            f"See docs/controls.md for recognized tool names."
                        ),
                    )
                )

        # Check require_any — at least one of the listed types must be present
        if cfg.require_any:
            if not any(rt in detected_types for rt in cfg.require_any):
                findings.append(
                    Finding(
                        control_id=self.control_id,
                        control_name=self.name,
                        severity=Severity.WARNING,
                        message=(
                            f"Missing at least one of: {', '.join(cfg.require_any)}"
                        ),
                        remediation=(
                            f"Add at least one of {cfg.require_any} stages to your pipeline."
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
    def _detect_stage_types(pipeline: PipelineModel) -> set[str]:
        """Detect which security stage types are present in the pipeline."""
        detected: set[str] = set()

        # Collect all names and scripts to search
        searchable_texts: list[str] = []
        for stage in pipeline.stages:
            searchable_texts.append(stage.name.lower())
            for step in stage.steps:
                searchable_texts.append(step.name.lower())
                searchable_texts.append(step.script.lower())
                if step.action:
                    searchable_texts.append(step.action.full_ref.lower())
                    searchable_texts.append(step.action.name.lower())

        combined_text = " ".join(searchable_texts)

        for stage_type, keywords in STAGE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in combined_text:
                    detected.add(stage_type)
                    break

        return detected
