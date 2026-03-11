"""Tests for reporters."""

from __future__ import annotations

import json

from spektci.config.schema import SpektciConfig
from spektci.core.result import (
    AnalysisResult,
    ControlResult,
    ControlStatus,
    Finding,
    Severity,
)
from spektci.reporters.json_reporter import JsonReporter
from spektci.reporters.sarif import SarifReporter
from spektci.reporters.terminal import TerminalReporter


def _make_result() -> AnalysisResult:
    return AnalysisResult(
        platform="github",
        project="test/repo",
        branch="main",
        control_results=[
            ControlResult(
                control_id="C001",
                control_name="Image tags",
                status=ControlStatus.PASS,
            ),
            ControlResult(
                control_id="C002",
                control_name="Image sources",
                status=ControlStatus.FAIL,
                findings=[
                    Finding(
                        control_id="C002",
                        control_name="Image sources",
                        severity=Severity.ERROR,
                        message="Unauthorized image: evil.com/malware:latest",
                        source_file="ci.yml",
                        source_line=10,
                    ),
                ],
            ),
        ],
    )


class TestTerminalReporter:
    def test_renders_output(self) -> None:
        reporter = TerminalReporter()
        result = _make_result()
        config = SpektciConfig()
        output = reporter.render(result, config)
        assert "spektci" in output
        assert "C001" in output
        assert "C002" in output
        assert "PASS" in output
        assert "FAIL" in output


class TestJsonReporter:
    def test_renders_valid_json(self) -> None:
        reporter = JsonReporter()
        result = _make_result()
        config = SpektciConfig()
        output = reporter.render(result, config)
        data = json.loads(output)
        assert data["platform"] == "github"
        assert data["project"] == "test/repo"
        assert len(data["controls"]) == 2
        assert data["summary"]["passed"] == 1
        assert data["summary"]["failed"] == 1


class TestSarifReporter:
    def test_renders_valid_sarif(self) -> None:
        reporter = SarifReporter()
        result = _make_result()
        config = SpektciConfig()
        output = reporter.render(result, config)
        data = json.loads(output)
        assert data["version"] == "2.1.0"
        assert len(data["runs"]) == 1
        run = data["runs"][0]
        assert run["tool"]["driver"]["name"] == "spektci"
        assert len(run["results"]) == 1
        assert run["results"][0]["ruleId"] == "C002"
