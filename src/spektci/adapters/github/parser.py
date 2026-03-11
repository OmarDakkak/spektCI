"""GitHub Actions YAML parser — normalizes workflow files into PipelineModel."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

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
            try:
                data = yaml.safe_load(content)
                if not isinstance(data, dict):
                    continue
            except yaml.YAMLError:
                logger.warning("Failed to parse YAML: %s", filename)
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

                stage = self._parse_job(job_name, job_data, filename)
                all_stages.append(stage)
                all_images.extend(stage.images)

                for step in stage.steps:
                    if step.action:
                        all_actions.append(step.action)

                # Job-level container images
                container = job_data.get("container")
                if container:
                    img = self._parse_container_image(container, filename)
                    if img:
                        all_images.append(img)

                # Services images
                services = job_data.get("services", {})
                if isinstance(services, dict):
                    for _svc_name, svc_data in services.items():
                        if isinstance(svc_data, dict) and "image" in svc_data:
                            img = self._parse_image_ref(svc_data["image"], filename)
                            if img:
                                all_images.append(img)

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
            action_ref = None
            script = ""

            # Parse `uses:` (action reference)
            uses = step_data.get("uses")
            if uses and isinstance(uses, str):
                action_ref = self._parse_action_ref(uses, filename)

                # Check for docker:// image references
                if uses.startswith("docker://"):
                    img = self._parse_image_ref(uses[9:], filename)
                    if img:
                        images.append(img)

            # Parse `run:` (inline script)
            run = step_data.get("run")
            if run and isinstance(run, str):
                script = run

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
    def _parse_action_ref(uses: str, filename: str) -> ActionReference:
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
        )

    def _parse_container_image(self, container: Any, filename: str) -> ContainerImage | None:
        """Parse a job-level container spec."""
        if isinstance(container, str):
            return self._parse_image_ref(container, filename)
        elif isinstance(container, dict) and "image" in container:
            return self._parse_image_ref(str(container["image"]), filename)
        return None

    @staticmethod
    def _parse_image_ref(ref: str, filename: str) -> ContainerImage | None:
        """Parse a container image reference string."""
        if not ref:
            return None

        match = IMAGE_TAG_RE.match(ref)
        if not match:
            return ContainerImage(full_ref=ref, source_file=filename)

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
            is_docker_official=is_official,
        )

    @staticmethod
    def _parse_permissions(perms: Any) -> PipelinePermissions:
        """Parse workflow-level permissions."""
        if isinstance(perms, str):
            return PipelinePermissions(top_level=perms)
        elif isinstance(perms, dict):
            return PipelinePermissions(top_level={str(k): str(v) for k, v in perms.items()})
        return PipelinePermissions()
