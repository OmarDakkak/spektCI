"""Tests for v0.2.0 improvements — C004 expression guard, SARIF severity,
ControlStatus enum, parser line numbers, reusable workflows, privileged
containers, terminal UX, CLI control filtering, and httpx resource cleanup.
"""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from spektci.adapters.base import RawPipelineData
from spektci.adapters.github.collector import GitHubCollector
from spektci.adapters.github.parser import GitHubParser
from spektci.cli.main import cli
from spektci.config.schema import SpektciConfig
from spektci.controls.hardcoded_secrets import HardcodedSecretsControl
from spektci.core.models import PipelineModel, PlatformType
from spektci.core.result import (
    AnalysisResult,
    ControlResult,
    ControlStatus,
    Finding,
    Severity,
)
from spektci.reporters.sarif import SarifReporter
from spektci.reporters.terminal import TerminalReporter

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "github"


# ── C004 Expression-Syntax Guard ────────────────────────────────────


class TestC004ExpressionGuard:
    """C004 must NOT flag CI/CD expression syntax like ${{ secrets.FOO }}."""

    def setup_method(self) -> None:
        self.control = HardcodedSecretsControl()
        self.config = SpektciConfig()

    def test_github_expression_not_flagged(self) -> None:
        """${{ secrets.MY_TOKEN }} must not trigger a false positive."""
        pipeline = PipelineModel(
            platform=PlatformType.GITHUB,
            project="test/repo",
            branch="main",
            raw_content={
                "ci.yml": (
                    'env:\n  TOKEN: "${{ secrets.MY_TOKEN }}"\n'
                    '  API_KEY: "${{ secrets.API_KEY }}"\n'
                )
            },
        )
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.PASS, (
            f"Should not flag expressions but got findings: {result.findings}"
        )

    def test_gitlab_ci_variable_not_flagged(self) -> None:
        """$CI_JOB_TOKEN and similar GitLab variables must not trigger."""
        pipeline = PipelineModel(
            platform=PlatformType.GITHUB,
            project="test/repo",
            branch="main",
            raw_content={
                "ci.yml": (
                    "script:\n"
                    '  - curl -H "Authorization: Bearer $CI_JOB_TOKEN" https://api.example.com\n'
                )
            },
        )
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.PASS

    def test_real_secret_still_flagged(self) -> None:
        """Actual hardcoded secrets must still be caught."""
        pipeline = PipelineModel(
            platform=PlatformType.GITHUB,
            project="test/repo",
            branch="main",
            raw_content={"ci.yml": "env:\n  TOKEN: ghp_abcdefghijklmnopqrstuvwxyz1234567890\n"},
        )
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.FAIL
        assert result.finding_count >= 1

    def test_mixed_line_expression_plus_secret(self) -> None:
        """A line with BOTH an expression AND a real secret should still flag."""
        pipeline = PipelineModel(
            platform=PlatformType.GITHUB,
            project="test/repo",
            branch="main",
            raw_content={
                "ci.yml": ('env:\n  COMBINED: "${{ secrets.A }}" password: "supersecretvalue123"\n')
            },
        )
        result = self.control.evaluate(pipeline, self.config)
        # The expression part is stripped, but the password pattern survives
        assert result.status == ControlStatus.FAIL


# ── ControlStatus StrEnum ────────────────────────────────────────


class TestControlStatusStrEnum:
    """ControlStatus must be a proper StrEnum."""

    def test_is_str_enum(self) -> None:
        assert issubclass(ControlStatus, str)
        # Must be iterable (StrEnum property)
        members = list(ControlStatus)
        assert ControlStatus.PASS in members
        assert ControlStatus.FAIL in members
        assert ControlStatus.SKIP in members
        assert ControlStatus.ERROR in members

    def test_values(self) -> None:
        assert ControlStatus.PASS == "pass"
        assert ControlStatus.FAIL == "fail"
        assert ControlStatus.SKIP == "skip"
        assert ControlStatus.ERROR == "error"

    def test_comparison(self) -> None:
        assert ControlStatus.PASS == "pass"
        assert ControlStatus.FAIL == "fail"


# ── SARIF Severity Mapping ──────────────────────────────────────


class TestSarifSeverityMapping:
    """SARIF rules and findings must respect per-finding severity."""

    def test_warning_finding_gets_warning_level(self) -> None:
        result = AnalysisResult(
            platform="github",
            project="test/repo",
            branch="main",
            control_results=[
                ControlResult(
                    control_id="C005",
                    control_name="Pinned actions",
                    status=ControlStatus.FAIL,
                    findings=[
                        Finding(
                            control_id="C005",
                            control_name="Pinned actions",
                            severity=Severity.WARNING,
                            message="Action not pinned",
                        ),
                    ],
                ),
            ],
        )
        reporter = SarifReporter()
        output = reporter.render(result, SpektciConfig())
        data = json.loads(output)

        run = data["runs"][0]
        # Rule default configuration should reflect WARNING
        rule = run["tool"]["driver"]["rules"][0]
        assert rule["defaultConfiguration"]["level"] == "warning"
        # Finding level
        assert run["results"][0]["level"] == "warning"

    def test_info_finding_gets_note_level(self) -> None:
        result = AnalysisResult(
            platform="github",
            project="test/repo",
            branch="main",
            control_results=[
                ControlResult(
                    control_id="C008",
                    control_name="Outdated deps",
                    status=ControlStatus.FAIL,
                    findings=[
                        Finding(
                            control_id="C008",
                            control_name="Outdated deps",
                            severity=Severity.INFO,
                            message="Slightly behind",
                        ),
                    ],
                ),
            ],
        )
        reporter = SarifReporter()
        output = reporter.render(result, SpektciConfig())
        data = json.loads(output)

        rule = data["runs"][0]["tool"]["driver"]["rules"][0]
        assert rule["defaultConfiguration"]["level"] == "note"
        assert data["runs"][0]["results"][0]["level"] == "note"

    def test_sarif_has_help_uri(self) -> None:
        result = AnalysisResult(
            platform="github",
            project="test/repo",
            branch="main",
            control_results=[
                ControlResult(
                    control_id="C001",
                    control_name="Image tags",
                    status=ControlStatus.PASS,
                ),
            ],
        )
        reporter = SarifReporter()
        output = reporter.render(result, SpektciConfig())
        data = json.loads(output)
        rule = data["runs"][0]["tool"]["driver"]["rules"][0]
        assert "helpUri" in rule
        assert "OmarDakkak" in rule["helpUri"]


# ── Parser: Line Numbers ────────────────────────────────────────


class TestParserLineNumbers:
    """Parser must extract line numbers from YAML using ruamel.yaml."""

    def setup_method(self) -> None:
        self.parser = GitHubParser()

    def test_steps_have_line_numbers(self) -> None:
        content = (FIXTURES_DIR / "compliant_workflow.yml").read_text()
        raw = RawPipelineData(
            config_files={".github/workflows/ci.yml": content},
            api_data={"default_branch": "main"},
            metadata={"repo": "test/repo"},
        )
        pipeline = self.parser.parse(raw)

        # At least one step should have a non-zero source_line
        steps_with_lines = [
            s for stage in pipeline.stages for s in stage.steps if s.source_line > 0
        ]
        assert len(steps_with_lines) > 0, "Steps should have line numbers from ruamel.yaml"

    def test_actions_have_line_numbers(self) -> None:
        content = (FIXTURES_DIR / "compliant_workflow.yml").read_text()
        raw = RawPipelineData(
            config_files={".github/workflows/ci.yml": content},
            api_data={"default_branch": "main"},
            metadata={"repo": "test/repo"},
        )
        pipeline = self.parser.parse(raw)
        actions_with_lines = [a for a in pipeline.actions if a.source_line > 0]
        assert len(actions_with_lines) > 0, "Actions should have line numbers"


# ── Parser: Reusable Workflows ──────────────────────────────────


class TestParserReusableWorkflows:
    """Parser must detect job-level `uses:` for reusable workflows."""

    def setup_method(self) -> None:
        self.parser = GitHubParser()

    def test_reusable_workflow_detected(self) -> None:
        content = (FIXTURES_DIR / "reusable_workflow.yml").read_text()
        raw = RawPipelineData(
            config_files={".github/workflows/ci.yml": content},
            api_data={"default_branch": "main"},
            metadata={"repo": "test/repo"},
        )
        pipeline = self.parser.parse(raw)

        reusable = [a for a in pipeline.actions if a.metadata.get("reusable_workflow")]
        assert len(reusable) >= 1
        assert reusable[0].owner == "org"
        assert "shared-workflows" in reusable[0].name

    def test_reusable_workflow_inline(self) -> None:
        yaml_content = """
name: Test
on: push
jobs:
  call-tests:
    uses: myorg/reusable/.github/workflows/test.yml@v1
  regular:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
"""
        raw = RawPipelineData(
            config_files={"ci.yml": yaml_content},
            api_data={},
            metadata={"repo": "test/repo"},
        )
        pipeline = self.parser.parse(raw)

        reusable = [a for a in pipeline.actions if a.metadata.get("reusable_workflow")]
        assert len(reusable) == 1
        regular = [a for a in pipeline.actions if not a.metadata.get("reusable_workflow")]
        assert len(regular) == 1


# ── Parser: Privileged Containers ───────────────────────────────


class TestParserPrivilegedContainers:
    """Parser must detect --privileged in container options."""

    def setup_method(self) -> None:
        self.parser = GitHubParser()

    def test_privileged_container_detected(self) -> None:
        content = (FIXTURES_DIR / "reusable_workflow.yml").read_text()
        raw = RawPipelineData(
            config_files={".github/workflows/ci.yml": content},
            api_data={"default_branch": "main"},
            metadata={"repo": "test/repo"},
        )
        pipeline = self.parser.parse(raw)
        assert pipeline.permissions.has_privileged_containers is True

    def test_non_privileged_container_not_flagged(self) -> None:
        yaml_content = """
name: Test
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    container:
      image: node:18
    steps:
      - uses: actions/checkout@v4
"""
        raw = RawPipelineData(
            config_files={"ci.yml": yaml_content},
            api_data={},
            metadata={"repo": "test/repo"},
        )
        pipeline = self.parser.parse(raw)
        assert pipeline.permissions.has_privileged_containers is False


# ── Terminal Reporter UX ────────────────────────────────────────


class TestTerminalReporterUX:
    """Terminal reporter should show compliance bar and file locations."""

    def test_compliance_bar_rendered(self) -> None:
        result = AnalysisResult(
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
                            message="Bad image",
                            source_file="ci.yml",
                            source_line=42,
                        ),
                    ],
                ),
            ],
        )
        reporter = TerminalReporter()
        output = reporter.render(result, SpektciConfig())
        # Compliance bar uses block characters
        assert "█" in output or "░" in output
        # File location should appear
        assert "ci.yml" in output
        assert "42" in output

    def test_control_name_always_shown(self) -> None:
        """Control name should appear regardless of findings."""
        result = AnalysisResult(
            platform="github",
            project="test/repo",
            branch="main",
            control_results=[
                ControlResult(
                    control_id="C001",
                    control_name="Image tags",
                    status=ControlStatus.FAIL,
                    findings=[
                        Finding(
                            control_id="C001",
                            control_name="Image tags",
                            severity=Severity.WARNING,
                            message="Uses latest tag",
                        ),
                    ],
                ),
            ],
        )
        reporter = TerminalReporter()
        output = reporter.render(result, SpektciConfig())
        assert "Image tags" in output


# ── GitHubCollector Resource Cleanup ────────────────────────────


class TestGitHubCollectorCleanup:
    """GitHubCollector must properly close httpx.Client."""

    def test_close_releases_client(self) -> None:
        config = SpektciConfig()
        collector = GitHubCollector(config)
        # Access client to create it
        _ = collector.client
        assert collector._client is not None
        collector.close()
        assert collector._client is None

    def test_context_manager(self) -> None:
        config = SpektciConfig()
        with GitHubCollector(config) as collector:
            _ = collector.client
            assert collector._client is not None
        # After exiting context, client should be closed
        assert collector._client is None

    def test_close_without_client_is_safe(self) -> None:
        config = SpektciConfig()
        collector = GitHubCollector(config)
        # Closing without ever creating a client should not raise
        collector.close()


# ── CLI --controls / --skip-controls ────────────────────────────


class TestCLIControlFiltering:
    """CLI should support --controls and --skip-controls flags."""

    def test_help_shows_controls_flag(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "--controls" in result.output
        assert "--skip-controls" in result.output

    def test_mutually_exclusive_flags(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "--controls", "C001", "--skip-controls", "C002"])
        assert result.exit_code != 0
        assert "mutually exclusive" in result.output.lower() or result.exit_code == 2
