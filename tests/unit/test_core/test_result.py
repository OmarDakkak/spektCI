"""Tests for core result types."""

from __future__ import annotations

import pytest

from spektci.core.result import (
    AnalysisResult,
    ControlResult,
    ControlStatus,
    Finding,
    Severity,
)


class TestSeverity:
    def test_ordering(self) -> None:
        assert Severity.ERROR > Severity.WARNING > Severity.INFO

    def test_from_string(self) -> None:
        assert Severity.from_string("error") == Severity.ERROR
        assert Severity.from_string("WARNING") == Severity.WARNING
        assert Severity.from_string("Info") == Severity.INFO

    def test_from_string_invalid(self) -> None:
        with pytest.raises(ValueError):
            Severity.from_string("critical")


class TestAnalysisResult:
    def test_compliance_score(self) -> None:
        result = AnalysisResult(
            platform="github",
            project="test/repo",
            branch="main",
            control_results=[
                ControlResult("C001", "Test 1", ControlStatus.PASS),
                ControlResult("C002", "Test 2", ControlStatus.FAIL),
                ControlResult("C003", "Test 3", ControlStatus.PASS),
                ControlResult("C004", "Test 4", ControlStatus.PASS),
            ],
        )
        assert result.compliance_score == 75.0
        assert result.passed_controls == 3
        assert result.failed_controls == 1

    def test_meets_threshold(self) -> None:
        result = AnalysisResult(
            platform="github",
            project="test/repo",
            branch="main",
            control_results=[
                ControlResult("C001", "Test", ControlStatus.PASS),
            ],
        )
        assert result.meets_threshold(100.0)
        assert result.meets_threshold(80.0)

    def test_empty_result_is_100_percent(self) -> None:
        result = AnalysisResult(
            platform="github",
            project="test/repo",
            branch="main",
        )
        assert result.compliance_score == 100.0

    def test_has_severity(self) -> None:
        result = AnalysisResult(
            platform="github",
            project="test/repo",
            branch="main",
            control_results=[
                ControlResult(
                    "C001",
                    "Test",
                    ControlStatus.FAIL,
                    findings=[
                        Finding("C001", "Test", Severity.WARNING, "warning msg"),
                    ],
                ),
            ],
        )
        assert result.has_severity_at_least(Severity.WARNING)
        assert not result.has_severity_at_least(Severity.ERROR)
