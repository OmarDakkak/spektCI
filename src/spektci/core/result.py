"""Analysis result types — Finding, Severity, AnalysisResult."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class Severity(IntEnum):
    """Finding severity levels, ordered from most to least severe."""

    ERROR = 3
    WARNING = 2
    INFO = 1

    @classmethod
    def from_string(cls, value: str) -> Severity:
        """Parse a severity string (case-insensitive)."""
        mapping = {
            "error": cls.ERROR,
            "warning": cls.WARNING,
            "info": cls.INFO,
        }
        normalized = value.strip().lower()
        if normalized not in mapping:
            raise ValueError(f"Unknown severity: {value!r}. Must be one of: error, warning, info")
        return mapping[normalized]

    def __str__(self) -> str:
        return self.name.lower()


class ControlStatus(str):
    """Status of a single control evaluation."""

    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"


@dataclass
class Finding:
    """A single compliance finding reported by a control."""

    control_id: str
    """Control identifier, e.g. 'C001'."""

    control_name: str
    """Human-readable control name."""

    severity: Severity
    """Finding severity."""

    message: str
    """Detailed finding message."""

    source_file: str = ""
    """File where the issue was found."""

    source_line: int = 0
    """Line number in the source file."""

    remediation: str = ""
    """Suggested remediation."""

    metadata: dict[str, object] = field(default_factory=dict)
    """Additional finding metadata."""


@dataclass
class ControlResult:
    """Result of evaluating a single compliance control."""

    control_id: str
    """Control identifier, e.g. 'C001'."""

    control_name: str
    """Human-readable control name."""

    status: str = ControlStatus.PASS
    """Overall status: pass, fail, skip, error."""

    findings: list[Finding] = field(default_factory=list)
    """Individual findings from this control."""

    error_message: str | None = None
    """Error message if the control failed to execute."""

    @property
    def passed(self) -> bool:
        """Return True if this control passed."""
        return self.status == ControlStatus.PASS

    @property
    def finding_count(self) -> int:
        """Number of findings."""
        return len(self.findings)


@dataclass
class AnalysisResult:
    """Complete result of a compliance analysis run."""

    platform: str
    """Platform that was analyzed."""

    project: str
    """Project identifier."""

    branch: str
    """Branch that was analyzed."""

    control_results: list[ControlResult] = field(default_factory=list)
    """Results from all evaluated controls."""

    @property
    def total_controls(self) -> int:
        """Total number of controls evaluated (excluding skipped)."""
        return sum(1 for r in self.control_results if r.status != ControlStatus.SKIP)

    @property
    def passed_controls(self) -> int:
        """Number of controls that passed."""
        return sum(1 for r in self.control_results if r.passed)

    @property
    def failed_controls(self) -> int:
        """Number of controls that failed."""
        return sum(1 for r in self.control_results if r.status == ControlStatus.FAIL)

    @property
    def compliance_score(self) -> float:
        """Compliance percentage (0-100). Returns 100.0 if no controls were evaluated."""
        total = self.total_controls
        if total == 0:
            return 100.0
        return (self.passed_controls / total) * 100.0

    @property
    def all_findings(self) -> list[Finding]:
        """Flat list of all findings across all controls."""
        findings: list[Finding] = []
        for result in self.control_results:
            findings.extend(result.findings)
        return findings

    def meets_threshold(self, threshold: float) -> bool:
        """Return True if the compliance score meets or exceeds the threshold."""
        return self.compliance_score >= threshold

    def has_severity_at_least(self, min_severity: Severity) -> bool:
        """Return True if any finding has severity >= min_severity."""
        return any(f.severity >= min_severity for f in self.all_findings)
