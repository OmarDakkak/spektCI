"""C004 — Pipeline must not contain hardcoded secrets."""

from __future__ import annotations

import re

from spektci.config.schema import SpektciConfig
from spektci.controls.base import BaseControl
from spektci.core.models import PipelineModel
from spektci.core.result import ControlResult, ControlStatus, Finding, Severity

# Built-in patterns for common secret/credential patterns
BUILTIN_PATTERNS: list[str] = [
    # Generic key=value with secret-like names
    r"(?i)(password|secret|token|api_key|apikey|access_key|private_key)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
    # GitHub PAT
    r"ghp_[a-zA-Z0-9]{36}",
    # GitLab PAT
    r"glpat-[a-zA-Z0-9\-]{20,}",
    # AWS Access Key ID
    r"AKIA[0-9A-Z]{16}",
    # Generic Bearer token
    r"Bearer\s+[a-zA-Z0-9\-._~+/]{20,}",
    # Generic basic auth
    r"(?i)https?://[^:]+:[^@]+@",
]


class HardcodedSecretsControl(BaseControl):
    """C004: Detect hardcoded secrets, tokens, or passwords in pipeline definitions."""

    @property
    def control_id(self) -> str:
        return "C004"

    @property
    def name(self) -> str:
        return "Pipeline must not contain hardcoded secrets"

    def evaluate(self, pipeline: PipelineModel, config: SpektciConfig) -> ControlResult:
        cfg = config.controls.hardcoded_secrets
        findings: list[Finding] = []

        # Compile all patterns (builtin + user-defined)
        all_patterns = BUILTIN_PATTERNS + cfg.patterns
        compiled = []
        for pattern_str in all_patterns:
            try:
                compiled.append(re.compile(pattern_str))
            except re.error:
                continue

        exclude = set(cfg.exclude_paths)

        for filename, content in pipeline.raw_content.items():
            if self._is_excluded(filename, exclude):
                continue

            for line_num, line in enumerate(content.splitlines(), start=1):
                for pattern in compiled:
                    match = pattern.search(line)
                    if match:
                        # Mask the matched secret in the message
                        matched_text = match.group()
                        masked = matched_text[:8] + "***" if len(matched_text) > 8 else "***"
                        findings.append(
                            Finding(
                                control_id=self.control_id,
                                control_name=self.name,
                                severity=Severity.ERROR,
                                message=(
                                    f"Possible secret detected in {filename} "
                                    f"line {line_num}: {masked}"
                                ),
                                source_file=filename,
                                source_line=line_num,
                                remediation=(
                                    "Move this value to an environment variable or "
                                    "secret manager. Never hardcode credentials in "
                                    "pipeline definitions."
                                ),
                            )
                        )
                        break  # One finding per line is enough

        return ControlResult(
            control_id=self.control_id,
            control_name=self.name,
            status=ControlStatus.FAIL if findings else ControlStatus.PASS,
            findings=findings,
        )

    @staticmethod
    def _is_excluded(filename: str, exclude_patterns: set[str]) -> bool:
        """Check if a filename matches any exclude pattern.

        Supports glob patterns including ``**`` for recursive matching.
        A ``**/`` prefix is treated as "match at any directory depth", so
        ``**/*.example.yml`` will also match a bare ``deploy.example.yml``.
        """
        import fnmatch

        for pattern in exclude_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
            # ``**/<rest>`` should also match files with no leading directory
            if pattern.startswith("**/"):
                sub = pattern[3:]
                if fnmatch.fnmatch(filename, sub):
                    return True
        return False
