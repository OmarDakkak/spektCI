"""GitHub Actions YAML parser — normalizes workflow files into PipelineModel."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

import ruamel.yaml
import yaml

from spektci.core.models import (
    ActionReference,
    ContainerImage,
    PipelineModel,
    PipelinePermissions,
    PipelineStage,
    PipelineStep,
    PlatformType,
)

if TYPE_CHECKING:
    from spektci.adapters.base import RawPipelineData

logger = logging.getLogger(__name__)

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
IMAGE_TAG_RE = re.compile(
    r"^(?:(?P<registry>[^/]+\.[^/]+)/)?(?P<repo>.+?)(?::(?P<tag>[^@]+))?(?:@(?P<digest>sha256:[a-f0-9]+))?$"
)

# ── Helpers for extracting line numbers from ruamel.yaml ────────

_ruamel = ruamel.yaml.YAML()
_ruamel.preserve_quotes = True


def _line_of(node: Any) -> int:
    """Return the 1-based line number for a ruamel.yaml node, or 0."""
    if hasattr(node, "lc"):
        return int(node.lc.line) + 1  # lc.line is 0-based
    return 0


def _safe_parse_ruamel(content: str) -> Any:
    """Parse YAML with ruamel.yaml for line tracking; fall back to PyYAML."""
    try:
        return _ruamel.load(content)
    except Exception:
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError:
            return None


class GitHubParser:
    """Parse GitHub Actions workflow YAML files into PipelineModel."""

    def parse(self, raw: RawPipelineData) -> PipelineModel:
        """Parse all collected workflow files into a single PipelineModel."""
        all_stages: list[PipelineStage] = []
        all_images: list[ContainerImage] = []
        all_actions: list[ActionReference] = []
        permissions = PipelinePermissions()

        repo = raw.metadata.get("repo", "")

        for filename, content in raw.config_files.items():
            data = _safe_parse_ruamel(content)
            if not isinstance(data, dict):
                continue

            # Parse top-level permissions
            if "permissions" in data:
                permissions = self._parse_permissions(data["permissions"])

            # Parse jobs
            jobs = data.get("jobs", {})
            if not isinstance(jobs, dict):
                continue

            for job_name, job_data in jobs.items():
                if not isinstance(job_data, dict):
                    continue

                # Detect reusable workflow calls (job-level `uses:`)
                job_uses = job_data.get("uses")
                if job_uses and isinstance(job_uses, str):
                    action_ref = self._parse_action_ref(str(job_uses), filename, _line_of(job_data))
                    action_ref.metadata["reusable_workflow"] = True
                    all_actions.append(action_ref)
                    all_stages.append(PipelineStage(name=str(job_name), steps=[], images=[]))
                    continue

                stage = self._parse_job(str(job_name), job_data, filename)
                all_stages.append(stage)
                all_images.extend(stage.images)

                for step in stage.steps:
                    if step.action:
                        all_actions.append(step.action)

                # Job-level container images
                container = job_data.get("container")
                if container:
                    img = self._parse_container_image(
                        container, filename, _line_of(container) if hasattr(container, "lc") else 0
                    )
                    if img:
                        all_images.append(img)

                    # Detect privileged mode from container options
                    if isinstance(container, dict):
                        options = container.get("options", "")
                        if isinstance(options, str) and "--privileged" in options:
                            permissions.has_privileged_containers = True

                # Services images
                services = job_data.get("services", {})
                if isinstance(services, dict):
                    for _svc_name, svc_data in services.items():
                        if isinstance(svc_data, dict) and "image" in svc_data:
                            img = self._parse_image_ref(
                                str(svc_data["image"]),
                                filename,
                                _line_of(svc_data),
                            )
                            if img:
                                all_images.append(img)

                        # Services can also be privileged
                        if isinstance(svc_data, dict):
                            svc_options = svc_data.get("options", "")
                            if isinstance(svc_options, str) and "--privileged" in svc_options:
                                permissions.has_privileged_containers = True

        return PipelineModel(
            platform=PlatformType.GITHUB,
            project=str(repo),
            branch=str(raw.api_data.get("default_branch", "main")),
            source_files=list(raw.config_files.keys()),
            stages=all_stages,
            images=all_images,
            actions=all_actions,
            permissions=permissions,
            raw_content=dict(raw.config_files),
        )

    def _parse_job(self, job_name: str, job_data: dict[str, Any], filename: str) -> PipelineStage:
        """Parse a single job into a PipelineStage."""
        steps: list[PipelineStep] = []
        images: list[ContainerImage] = []

        raw_steps = job_data.get("steps", [])
        if not isinstance(raw_steps, list):
            raw_steps = []

        for i, step_data in enumerate(raw_steps):
            if not isinstance(step_data, dict):
                continue

            step_name = step_data.get("name", f"step-{i}")
            step_line = _line_of(step_data)
            action_ref = None
            script = ""

            # Parse `uses:` (action reference)
            uses = step_data.get("uses")
            if uses and isinstance(uses, str):
                action_ref = self._parse_action_ref(str(uses), filename, step_line)

                # Check for docker:// image references
                if str(uses).startswith("docker://"):
                    img = self._parse_image_ref(str(uses)[9:], filename, step_line)
                    if img:
                        images.append(img)

            # Parse `run:` (inline script)
            run = step_data.get("run")
            if run and isinstance(run, str):
                script = str(run)

            # Parse step environment
            env = step_data.get("env", {})
            if not isinstance(env, dict):
                env = {}

            steps.append(
                PipelineStep(
                    name=str(step_name),
                    action=action_ref,
                    script=script,
                    environment={str(k): str(v) for k, v in env.items()},
                    source_file=filename,
                    source_line=step_line,
                )
            )

        return PipelineStage(
            name=job_name,
            steps=steps,
            images=images,
            environment={str(k): str(v) for k, v in job_data.get("env", {}).items()}
            if isinstance(job_data.get("env"), dict)
            else {},
        )

    @staticmethod
    def _parse_action_ref(uses: str, filename: str, line: int = 0) -> ActionReference:
        """Parse a GitHub Actions `uses:` reference.

        Formats:
        - owner/repo@ref
        - owner/repo/path@ref
        - ./local-action
        - docker://image:tag
        """
        if uses.startswith("./") or uses.startswith("docker://"):
            return ActionReference(
                full_ref=uses,
                name=uses,
                source_file=filename,
                source_line=line,
            )

        # Split on @ to get ref
        if "@" in uses:
            action_path, version = uses.rsplit("@", 1)
        else:
            action_path = uses
            version = ""

        # Split owner/name
        parts = action_path.split("/", 2)
        owner = parts[0] if len(parts) > 1 else ""
        name = parts[1] if len(parts) > 1 else parts[0]

        is_sha = bool(SHA_RE.match(version))

        return ActionReference(
            full_ref=uses,
            owner=owner,
            name=name,
            version=version,
            is_sha_pinned=is_sha,
            source_file=filename,
            source_line=line,
        )

    def _parse_container_image(
        self, container: Any, filename: str, line: int = 0
    ) -> ContainerImage | None:
        """Parse a job-level container spec."""
        if isinstance(container, str):
            return self._parse_image_ref(str(container), filename, line)
        elif isinstance(container, dict) and "image" in container:
            return self._parse_image_ref(
                str(container["image"]), filename, _line_of(container) or line
            )
        return None

    @staticmethod
    def _parse_image_ref(ref: str, filename: str, line: int = 0) -> ContainerImage | None:
        """Parse a container image reference string."""
        if not ref:
            return None

        match = IMAGE_TAG_RE.match(ref)
        if not match:
            return ContainerImage(full_ref=ref, source_file=filename, source_line=line)

        registry = match.group("registry")
        repository = match.group("repo") or ""
        tag = match.group("tag")
        digest = match.group("digest")

        # Detect Docker official images
        is_official = (registry is None or registry == "docker.io") and "/" not in repository

        # Default tag
        if not tag and not digest:
            tag = "latest"

        return ContainerImage(
            full_ref=ref,
            registry=registry,
            repository=repository,
            tag=tag,
            digest=digest,
            source_file=filename,
            source_line=line,
            is_docker_official=is_official,
        )

    @staticmethod
    def _parse_permissions(perms: Any) -> PipelinePermissions:
        """Parse workflow-level permissions."""
        if isinstance(perms, str):
            return PipelinePermissions(top_level=str(perms))
        elif isinstance(perms, dict):
            return PipelinePermissions(top_level={str(k): str(v) for k, v in perms.items()})
        return PipelinePermissions()
