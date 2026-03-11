"""Tests for the GitHub Actions parser."""

from __future__ import annotations

from pathlib import Path

from spektci.adapters.base import RawPipelineData
from spektci.adapters.github.parser import GitHubParser
from spektci.core.models import PlatformType

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "github"


class TestGitHubParser:
    """Tests for GitHub Actions YAML parser."""

    def setup_method(self) -> None:
        self.parser = GitHubParser()

    def test_parse_compliant_workflow(self) -> None:
        content = (FIXTURES_DIR / "compliant_workflow.yml").read_text()
        raw = RawPipelineData(
            config_files={".github/workflows/ci.yml": content},
            api_data={"default_branch": "main"},
            metadata={"repo": "test/repo"},
        )
        pipeline = self.parser.parse(raw)

        assert pipeline.platform == PlatformType.GITHUB
        assert pipeline.project == "test/repo"
        assert len(pipeline.stages) == 4  # build, test, sast, secret_scanning
        assert len(pipeline.actions) > 0

    def test_parse_noncompliant_workflow(self) -> None:
        content = (FIXTURES_DIR / "noncompliant_workflow.yml").read_text()
        raw = RawPipelineData(
            config_files={".github/workflows/deploy.yml": content},
            api_data={"default_branch": "main"},
            metadata={"repo": "test/repo"},
        )
        pipeline = self.parser.parse(raw)

        assert pipeline.platform == PlatformType.GITHUB
        assert len(pipeline.images) >= 1  # at least the container image

        # Check that the permissions were parsed
        assert pipeline.permissions.top_level == "write-all"

        # Check that mutable action ref was captured
        mutable_actions = [a for a in pipeline.actions if a.version == "main"]
        assert len(mutable_actions) >= 1

    def test_parse_action_ref_with_sha(self) -> None:
        ref = self.parser._parse_action_ref(
            "actions/checkout@a81bbbf8298c0fa03ea29cdc473d45769f953675",
            "test.yml",
        )
        assert ref.owner == "actions"
        assert ref.name == "checkout"
        assert ref.is_sha_pinned is True

    def test_parse_docker_image_ref(self) -> None:
        img = self.parser._parse_image_ref("ghcr.io/myorg/myimage:1.2.3", "test.yml")
        assert img is not None
        assert img.registry == "ghcr.io"
        assert img.repository == "myorg/myimage"
        assert img.tag == "1.2.3"

    def test_parse_image_defaults_to_latest(self) -> None:
        img = self.parser._parse_image_ref("python", "test.yml")
        assert img is not None
        assert img.tag == "latest"
        assert img.is_docker_official is True
