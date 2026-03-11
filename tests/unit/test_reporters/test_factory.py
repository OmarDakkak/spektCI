"""Tests for reporters factory and defaults generator."""

from __future__ import annotations

import pytest

from spektci.config.defaults import generate_default_config
from spektci.reporters import get_reporter
from spektci.reporters.json_reporter import JsonReporter
from spektci.reporters.sarif import SarifReporter
from spektci.reporters.terminal import TerminalReporter


class TestGetReporter:
    """Tests for the reporter factory function."""

    def test_terminal_reporter(self) -> None:
        reporter = get_reporter("terminal")
        assert isinstance(reporter, TerminalReporter)

    def test_json_reporter(self) -> None:
        reporter = get_reporter("json")
        assert isinstance(reporter, JsonReporter)

    def test_sarif_reporter(self) -> None:
        reporter = get_reporter("sarif")
        assert isinstance(reporter, SarifReporter)

    def test_unknown_format_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown output format"):
            get_reporter("xml")


class TestDefaultConfig:
    """Tests for default configuration generation."""

    def test_generates_valid_yaml(self) -> None:
        import yaml

        content = generate_default_config()
        assert isinstance(content, str)
        data = yaml.safe_load(content)
        assert data["version"] == "1"
        assert "global" in data
        assert "controls" in data
        assert "platform" in data

    def test_default_threshold(self) -> None:
        content = generate_default_config()
        assert "threshold: 80" in content

    def test_contains_all_controls(self) -> None:
        content = generate_default_config()
        for control in [
            "image_tags",
            "image_sources",
            "branch_protection",
            "hardcoded_secrets",
            "pinned_actions",
            "required_stages",
            "permissions",
            "outdated_deps",
        ]:
            assert control in content
