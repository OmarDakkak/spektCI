"""Platform adapters for CI/CD systems."""

from __future__ import annotations

from typing import TYPE_CHECKING

from spektci.adapters.detector import detect_platform

if TYPE_CHECKING:
    from spektci.adapters.base import BasePlatformAdapter
    from spektci.config.schema import SpektciConfig


def get_adapter(config: SpektciConfig) -> BasePlatformAdapter:
    """Resolve the appropriate platform adapter based on config.

    If ``config.platform.type`` is ``"auto"``, the platform is detected
    from the current git remote URL.

    Returns:
        An instantiated platform adapter.

    Raises:
        ValueError: If the platform cannot be detected or is not supported.
    """
    platform_type: str = config.platform.type

    if platform_type == "auto":
        platform_type = detect_platform()

    if platform_type == "github":
        from spektci.adapters.github.adapter import GitHubAdapter

        return GitHubAdapter(config)
    elif platform_type == "jenkins":
        from spektci.adapters.jenkins.adapter import JenkinsAdapter

        return JenkinsAdapter(config)
    elif platform_type == "bitbucket":
        from spektci.adapters.bitbucket.adapter import BitbucketAdapter

        return BitbucketAdapter(config)
    elif platform_type == "azure":
        from spektci.adapters.azure.adapter import AzureDevOpsAdapter

        return AzureDevOpsAdapter(config)
    elif platform_type == "circleci":
        from spektci.adapters.circleci.adapter import CircleCIAdapter

        return CircleCIAdapter(config)
    else:
        raise ValueError(f"Unsupported platform: {platform_type}")
