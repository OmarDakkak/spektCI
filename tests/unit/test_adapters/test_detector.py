"""Tests for platform detection and adapter factory."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from spektci.adapters import get_adapter
from spektci.adapters.detector import (
    _get_git_remote_url,
    detect_platform,
    get_repo_from_remote,
)
from spektci.config.schema import SpektciConfig


class TestDetectPlatform:
    """Tests for auto-detection of CI/CD platform from git remote."""

    @patch("spektci.adapters.detector._get_git_remote_url")
    def test_detects_github(self, mock_remote: object) -> None:
        mock_remote.return_value = "git@github.com:owner/repo.git"  # type: ignore[union-attr]
        assert detect_platform() == "github"

    @patch("spektci.adapters.detector._get_git_remote_url")
    def test_detects_github_https(self, mock_remote: object) -> None:
        mock_remote.return_value = "https://github.com/owner/repo.git"  # type: ignore[union-attr]
        assert detect_platform() == "github"

    @patch("spektci.adapters.detector._get_git_remote_url")
    def test_detects_bitbucket(self, mock_remote: object) -> None:
        mock_remote.return_value = "git@bitbucket.org:owner/repo.git"  # type: ignore[union-attr]
        assert detect_platform() == "bitbucket"

    @patch("spektci.adapters.detector._get_git_remote_url")
    def test_detects_azure(self, mock_remote: object) -> None:
        mock_remote.return_value = "https://dev.azure.com/org/project/_git/repo"  # type: ignore[union-attr]
        assert detect_platform() == "azure"

    @patch("spektci.adapters.detector._get_git_remote_url")
    def test_raises_on_no_remote(self, mock_remote: object) -> None:
        mock_remote.return_value = None  # type: ignore[union-attr]
        with pytest.raises(ValueError, match="no git remote found"):
            detect_platform()

    @patch("spektci.adapters.detector._get_git_remote_url")
    def test_raises_on_unknown_remote(self, mock_remote: object) -> None:
        mock_remote.return_value = "https://selfhosted.example.com/repo.git"  # type: ignore[union-attr]
        with pytest.raises(ValueError, match="Could not detect platform"):
            detect_platform()


class TestGetRepoFromRemote:
    """Tests for extracting owner/repo from git remote URL."""

    @patch("spektci.adapters.detector._get_git_remote_url")
    def test_ssh_url(self, mock_remote: object) -> None:
        mock_remote.return_value = "git@github.com:owner/repo.git"  # type: ignore[union-attr]
        assert get_repo_from_remote() == "owner/repo"

    @patch("spektci.adapters.detector._get_git_remote_url")
    def test_https_url(self, mock_remote: object) -> None:
        mock_remote.return_value = "https://github.com/owner/repo.git"  # type: ignore[union-attr]
        assert get_repo_from_remote() == "owner/repo"

    @patch("spektci.adapters.detector._get_git_remote_url")
    def test_no_remote(self, mock_remote: object) -> None:
        mock_remote.return_value = None  # type: ignore[union-attr]
        assert get_repo_from_remote() is None


class TestGetGitRemoteUrl:
    """Tests for _get_git_remote_url subprocess call."""

    @patch("spektci.adapters.detector.subprocess.run")
    def test_success(self, mock_run: object) -> None:
        mock_run.return_value.returncode = 0  # type: ignore[union-attr]
        mock_run.return_value.stdout = "https://github.com/owner/repo.git\n"  # type: ignore[union-attr]
        assert _get_git_remote_url() == "https://github.com/owner/repo.git"

    @patch("spektci.adapters.detector.subprocess.run")
    def test_failure(self, mock_run: object) -> None:
        mock_run.return_value.returncode = 1  # type: ignore[union-attr]
        assert _get_git_remote_url() is None

    @patch("spektci.adapters.detector.subprocess.run", side_effect=FileNotFoundError)
    def test_git_not_found(self, mock_run: object) -> None:
        assert _get_git_remote_url() is None


class TestGetAdapter:
    """Tests for get_adapter factory function."""

    def test_github_adapter(self) -> None:
        config = SpektciConfig()
        config.platform.type = "github"  # type: ignore[assignment]
        adapter = get_adapter(config)
        assert adapter.__class__.__name__ == "GitHubAdapter"

    def test_jenkins_adapter(self) -> None:
        config = SpektciConfig()
        config.platform.type = "jenkins"  # type: ignore[assignment]
        adapter = get_adapter(config)
        assert adapter.__class__.__name__ == "JenkinsAdapter"

    def test_bitbucket_adapter(self) -> None:
        config = SpektciConfig()
        config.platform.type = "bitbucket"  # type: ignore[assignment]
        adapter = get_adapter(config)
        assert adapter.__class__.__name__ == "BitbucketAdapter"

    def test_azure_adapter(self) -> None:
        config = SpektciConfig()
        config.platform.type = "azure"  # type: ignore[assignment]
        adapter = get_adapter(config)
        assert adapter.__class__.__name__ == "AzureDevOpsAdapter"

    def test_circleci_adapter(self) -> None:
        config = SpektciConfig()
        config.platform.type = "circleci"  # type: ignore[assignment]
        adapter = get_adapter(config)
        assert adapter.__class__.__name__ == "CircleCIAdapter"

    def test_unsupported_platform_raises(self) -> None:
        config = SpektciConfig()
        config.platform.type = "unknown"  # type: ignore[assignment]
        with pytest.raises(ValueError, match="Unsupported platform"):
            get_adapter(config)


class TestStubAdapters:
    """Tests for stub adapter implementations."""

    def test_azure_collect_raises(self) -> None:
        from spektci.adapters.azure.adapter import AzureDevOpsAdapter

        config = SpektciConfig()
        adapter = AzureDevOpsAdapter(config)
        with pytest.raises(NotImplementedError):
            adapter.collect(config)

    def test_azure_detect(self) -> None:
        from spektci.adapters.azure.adapter import AzureDevOpsAdapter

        config = SpektciConfig()
        adapter = AzureDevOpsAdapter(config)
        assert adapter.detect("https://dev.azure.com/org/proj")
        assert not adapter.detect("https://github.com/org/proj")

    def test_jenkins_collect_raises(self) -> None:
        from spektci.adapters.jenkins.adapter import JenkinsAdapter

        config = SpektciConfig()
        adapter = JenkinsAdapter(config)
        with pytest.raises(NotImplementedError):
            adapter.collect(config)

    def test_bitbucket_collect_raises(self) -> None:
        from spektci.adapters.bitbucket.adapter import BitbucketAdapter

        config = SpektciConfig()
        adapter = BitbucketAdapter(config)
        with pytest.raises(NotImplementedError):
            adapter.collect(config)

    def test_circleci_collect_raises(self) -> None:
        from spektci.adapters.circleci.adapter import CircleCIAdapter

        config = SpektciConfig()
        adapter = CircleCIAdapter(config)
        with pytest.raises(NotImplementedError):
            adapter.collect(config)
