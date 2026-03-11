"""Tests for C004 — Hardcoded secrets control."""

from __future__ import annotations

from spektci.config.schema import SpektciConfig
from spektci.controls.hardcoded_secrets import HardcodedSecretsControl
from spektci.core.models import PipelineModel, PlatformType
from spektci.core.result import ControlStatus


class TestHardcodedSecretsControl:
    """Tests for C004."""

    def setup_method(self) -> None:
        self.control = HardcodedSecretsControl()
        self.config = SpektciConfig()

    def test_passes_when_no_secrets(self) -> None:
        pipeline = PipelineModel(
            platform=PlatformType.GITHUB,
            project="test/repo",
            branch="main",
            raw_content={
                "ci.yml": "name: CI\non: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n"
            },
        )
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.PASS

    def test_detects_hardcoded_password(self) -> None:
        pipeline = PipelineModel(
            platform=PlatformType.GITHUB,
            project="test/repo",
            branch="main",
            raw_content={"deploy.yml": 'env:\n  PASSWORD: "mysupersecretvalue123"\n'},
        )
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.FAIL
        assert result.finding_count >= 1

    def test_detects_github_token(self) -> None:
        pipeline = PipelineModel(
            platform=PlatformType.GITHUB,
            project="test/repo",
            branch="main",
            raw_content={"deploy.yml": "TOKEN=ghp_abcdefghijklmnopqrstuvwxyz1234567890\n"},
        )
        result = self.control.evaluate(pipeline, self.config)
        assert result.status == ControlStatus.FAIL
        assert result.finding_count >= 1

    def test_respects_exclude_paths(self) -> None:
        config = SpektciConfig()
        config.controls.hardcoded_secrets.exclude_paths = ["**/*.example.yml"]
        pipeline = PipelineModel(
            platform=PlatformType.GITHUB,
            project="test/repo",
            branch="main",
            raw_content={"deploy.example.yml": 'env:\n  PASSWORD: "supersecretvalue123"\n'},
        )
        result = self.control.evaluate(pipeline, config)
        assert result.status == ControlStatus.PASS
