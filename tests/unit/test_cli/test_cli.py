"""Tests for CLI commands using Click's CliRunner."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from spektci.cli.main import cli
from spektci.core.result import AnalysisResult, ControlResult, ControlStatus


class TestCliMain:
    """Tests for the main CLI group."""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    def test_version_flag(self) -> None:
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "spektci" in result.output

    def test_help_flag(self) -> None:
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "analyze" in result.output
        assert "config" in result.output

    def test_verbose_flag(self) -> None:
        result = self.runner.invoke(cli, ["--verbose", "--help"])
        assert result.exit_code == 0


class TestCliConfig:
    """Tests for `spektci config` subcommands."""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    def test_config_init(self) -> None:
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["config", "init"])
            assert result.exit_code == 0
            assert "✓" in result.output
            assert Path(".spektci.yaml").exists()

    def test_config_init_custom_output(self) -> None:
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["config", "init", "--output", "custom.yaml"])
            assert result.exit_code == 0
            assert Path("custom.yaml").exists()

    def test_config_init_no_overwrite(self) -> None:
        with self.runner.isolated_filesystem():
            Path(".spektci.yaml").write_text("existing", encoding="utf-8")
            result = self.runner.invoke(cli, ["config", "init"])
            assert result.exit_code == 1
            assert "already exists" in result.output

    def test_config_init_force(self) -> None:
        with self.runner.isolated_filesystem():
            Path(".spektci.yaml").write_text("existing", encoding="utf-8")
            result = self.runner.invoke(cli, ["config", "init", "--force"])
            assert result.exit_code == 0

    def test_config_init_with_platform(self) -> None:
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["config", "init", "--platform", "github"])
            assert result.exit_code == 0
            content = Path(".spektci.yaml").read_text()
            assert "type: github" in content

    def test_config_validate_valid(self) -> None:
        with self.runner.isolated_filesystem():
            # First create a config
            self.runner.invoke(cli, ["config", "init"])
            result = self.runner.invoke(cli, ["config", "validate", "-c", ".spektci.yaml"])
            assert result.exit_code == 0
            assert "✓" in result.output

    def test_config_validate_missing(self) -> None:
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["config", "validate", "-c", "nonexistent.yaml"])
            assert result.exit_code == 2

    def test_config_view(self) -> None:
        with self.runner.isolated_filesystem():
            self.runner.invoke(cli, ["config", "init"])
            result = self.runner.invoke(cli, ["config", "view", "-c", ".spektci.yaml", "--no-color"])
            assert result.exit_code == 0
            assert "threshold" in result.output

    def test_config_view_missing(self) -> None:
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["config", "view", "-c", "missing.yaml"])
            assert result.exit_code == 2


class TestCliAnalyze:
    """Tests for `spektci analyze` command."""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    def test_analyze_config_error(self) -> None:
        with self.runner.isolated_filesystem():
            Path(".spektci.yaml").write_text("invalid: {{{", encoding="utf-8")
            result = self.runner.invoke(cli, ["analyze", "--config", ".spektci.yaml"])
            assert result.exit_code == 2

    @patch("spektci.cli.analyze.get_adapter")
    @patch("spektci.cli.analyze.load_config")
    def test_analyze_platform_error(
        self, mock_load: MagicMock, mock_adapter: MagicMock
    ) -> None:
        from spektci.config.schema import SpektciConfig

        mock_load.return_value = SpektciConfig()
        mock_adapter.side_effect = ValueError("Unsupported platform")
        result = self.runner.invoke(cli, ["analyze"])
        assert result.exit_code == 2
        assert "Platform error" in result.output

    @patch("spektci.cli.analyze.get_reporter")
    @patch("spektci.cli.analyze.AnalysisEngine")
    @patch("spektci.cli.analyze.get_enabled_controls")
    @patch("spektci.cli.analyze.get_adapter")
    @patch("spektci.cli.analyze.load_config")
    def test_analyze_success(
        self,
        mock_load: MagicMock,
        mock_adapter: MagicMock,
        mock_controls: MagicMock,
        mock_engine_cls: MagicMock,
        mock_reporter: MagicMock,
    ) -> None:
        from spektci.config.schema import SpektciConfig

        mock_load.return_value = SpektciConfig()
        mock_controls.return_value = []
        mock_adapter.return_value = MagicMock()

        analysis_result = AnalysisResult(
            platform="github",
            project="test/repo",
            branch="main",
            control_results=[
                ControlResult(
                    control_id="C001",
                    control_name="Test",
                    status=ControlStatus.PASS,
                )
            ],
        )
        mock_engine_cls.return_value.run.return_value = analysis_result
        mock_reporter.return_value.render.return_value = "report output"

        result = self.runner.invoke(cli, ["analyze"])
        assert result.exit_code == 0
