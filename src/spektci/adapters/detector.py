"""Auto-detect CI/CD platform from git remote URL."""

from __future__ import annotations

import logging
import re
import subprocess

logger = logging.getLogger(__name__)

# Patterns to detect platform from git remote URLs
PLATFORM_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("github", re.compile(r"github\.com[:/]")),
    ("bitbucket", re.compile(r"bitbucket\.org[:/]")),
    ("azure", re.compile(r"dev\.azure\.com[:/]|visualstudio\.com[:/]")),
    # GitLab is not supported yet, but included for detection
    ("gitlab", re.compile(r"gitlab\.com[:/]")),
]


def detect_platform() -> str:
    """Detect the CI/CD platform from the current git remote URL.

    Returns:
        Platform identifier string (e.g. 'github', 'bitbucket').

    Raises:
        ValueError: If the platform cannot be detected.
    """
    remote_url = _get_git_remote_url()
    if not remote_url:
        raise ValueError(
            "Could not detect platform: no git remote found. "
            "Use --platform to specify the platform explicitly."
        )

    for platform, pattern in PLATFORM_PATTERNS:
        if pattern.search(remote_url):
            logger.info("Detected platform '%s' from remote: %s", platform, remote_url)
            return platform

    raise ValueError(
        f"Could not detect platform from remote URL: {remote_url}. "
        f"Use --platform to specify the platform explicitly."
    )


def get_repo_from_remote() -> str | None:
    """Extract the owner/repo from the git remote URL.

    Returns:
        Repository path like 'owner/repo', or None if not determinable.
    """
    remote_url = _get_git_remote_url()
    if not remote_url:
        return None

    # Handle SSH and HTTPS formats
    # SSH: git@github.com:owner/repo.git
    # HTTPS: https://github.com/owner/repo.git
    match = re.search(r"[:/]([^/]+/[^/]+?)(?:\.git)?$", remote_url)
    if match:
        return match.group(1)

    return None


def _get_git_remote_url() -> str | None:
    """Get the origin remote URL from git."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    return None
