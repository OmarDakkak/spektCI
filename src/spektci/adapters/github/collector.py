"""GitHub API client — collects workflow files and repo settings."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import httpx

from spektci.adapters.base import RawPipelineData
from spektci.config.schema import SpektciConfig
from spektci.core.models import BranchProtection

logger = logging.getLogger(__name__)

DEFAULT_API_URL = "https://api.github.com"
WORKFLOW_DIR = ".github/workflows"


class GitHubCollector:
    """Collects pipeline data from GitHub via REST API and local files."""

    def __init__(self, config: SpektciConfig) -> None:
        self.api_url = config.platform.api_url or DEFAULT_API_URL
        self.token = os.environ.get("GITHUB_TOKEN")
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Lazily create an HTTP client."""
        if self._client is None:
            headers: dict[str, str] = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            self._client = httpx.Client(
                base_url=self.api_url,
                headers=headers,
                timeout=30.0,
            )
        return self._client

    def collect(self, repo: str) -> RawPipelineData:
        """Collect workflow files and repository metadata.

        Tries local files first, falls back to API.
        """
        config_files: dict[str, str] = {}
        api_data: dict[str, object] = {}

        # Try local workflow files first
        local_workflows = self._collect_local_workflows()
        if local_workflows:
            config_files.update(local_workflows)
        else:
            # Fall back to API
            api_workflows = self._collect_api_workflows(repo)
            config_files.update(api_workflows)

        # Fetch repo metadata from API
        try:
            repo_info = self._get_repo_info(repo)
            api_data["repo"] = repo_info
            api_data["default_branch"] = repo_info.get("default_branch", "main")
        except Exception:
            logger.warning("Could not fetch repo info for %s", repo)
            api_data["default_branch"] = "main"

        return RawPipelineData(
            config_files=config_files,
            api_data=api_data,
            metadata={"repo": repo},
        )

    def get_branch_protection(self, repo: str, branch: str) -> BranchProtection:
        """Fetch branch protection rules from GitHub API."""
        try:
            resp = self.client.get(f"/repos/{repo}/branches/{branch}/protection")
            if resp.status_code == 404:
                return BranchProtection(branch=branch, is_protected=False)

            resp.raise_for_status()
            data = resp.json()

            # Parse protection settings
            pr_reviews = data.get("required_pull_request_reviews", {})
            status_checks = data.get("required_status_checks", {})

            return BranchProtection(
                branch=branch,
                is_protected=True,
                require_pr_review=pr_reviews is not None and bool(pr_reviews),
                min_approvals=pr_reviews.get(
                    "required_approving_review_count", 0
                ) if pr_reviews else 0,
                require_status_checks=status_checks is not None and bool(status_checks),
                required_checks=(
                    [c.get("context", "") for c in status_checks.get("checks", [])]
                    if status_checks else []
                ),
                block_force_push=data.get("allow_force_pushes", {}).get("enabled") is False,
                block_deletions=data.get("allow_deletions", {}).get("enabled") is False,
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return BranchProtection(branch=branch, is_protected=False)
            raise
        except Exception:
            logger.warning("Could not fetch branch protection for %s/%s", repo, branch)
            return BranchProtection(branch=branch, is_protected=False)

    def _collect_local_workflows(self) -> dict[str, str]:
        """Read workflow files from the local .github/workflows directory."""
        workflows: dict[str, str] = {}
        workflow_dir = Path(WORKFLOW_DIR)

        if not workflow_dir.is_dir():
            return workflows

        for path in workflow_dir.glob("*.yml"):
            try:
                content = path.read_text(encoding="utf-8")
                workflows[str(path)] = content
            except OSError:
                logger.warning("Could not read workflow file: %s", path)

        for path in workflow_dir.glob("*.yaml"):
            try:
                content = path.read_text(encoding="utf-8")
                workflows[str(path)] = content
            except OSError:
                logger.warning("Could not read workflow file: %s", path)

        return workflows

    def _collect_api_workflows(self, repo: str) -> dict[str, str]:
        """Fetch workflow files from the GitHub API."""
        workflows: dict[str, str] = {}

        try:
            # List files in .github/workflows/
            resp = self.client.get(
                f"/repos/{repo}/contents/{WORKFLOW_DIR}"
            )
            resp.raise_for_status()
            files = resp.json()

            for file_info in files:
                if not file_info["name"].endswith((".yml", ".yaml")):
                    continue

                # Fetch file content
                file_resp = self.client.get(file_info["download_url"])
                file_resp.raise_for_status()
                workflows[file_info["path"]] = file_resp.text

        except httpx.HTTPStatusError:
            logger.warning("Could not fetch workflows from API for %s", repo)
        except Exception:
            logger.warning("Error fetching workflows from API for %s", repo)

        return workflows

    def _get_repo_info(self, repo: str) -> dict[str, object]:
        """Fetch repository metadata."""
        resp = self.client.get(f"/repos/{repo}")
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]
