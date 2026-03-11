"""Control auto-discovery and registry."""

from __future__ import annotations

from spektci.config.schema import SpektciConfig
from spektci.controls.base import BaseControl
from spektci.controls.branch_protection import BranchProtectionControl
from spektci.controls.hardcoded_secrets import HardcodedSecretsControl
from spektci.controls.image_sources import ImageSourcesControl
from spektci.controls.image_tags import ImageTagsControl
from spektci.controls.outdated_deps import OutdatedDepsControl
from spektci.controls.permissions import PermissionsControl
from spektci.controls.pinned_actions import PinnedActionsControl
from spektci.controls.required_stages import RequiredStagesControl

# Ordered list of all available controls
ALL_CONTROLS: list[type[BaseControl]] = [
    ImageTagsControl,        # C001
    ImageSourcesControl,     # C002
    BranchProtectionControl, # C003
    HardcodedSecretsControl, # C004
    PinnedActionsControl,    # C005
    RequiredStagesControl,   # C006
    PermissionsControl,      # C007
    OutdatedDepsControl,     # C008
]


def get_all_controls() -> list[BaseControl]:
    """Return instances of all registered controls."""
    return [cls() for cls in ALL_CONTROLS]


def get_enabled_controls(config: SpektciConfig) -> list[BaseControl]:
    """Return instances of controls that are enabled in the config."""
    enabled_map: dict[str, bool] = {
        "C001": config.controls.image_tags.enabled,
        "C002": config.controls.image_sources.enabled,
        "C003": config.controls.branch_protection.enabled,
        "C004": config.controls.hardcoded_secrets.enabled,
        "C005": config.controls.pinned_actions.enabled,
        "C006": config.controls.required_stages.enabled,
        "C007": config.controls.permissions.enabled,
        "C008": config.controls.outdated_deps.enabled,
    }

    controls: list[BaseControl] = []
    for cls in ALL_CONTROLS:
        instance = cls()
        if enabled_map.get(instance.control_id, True):
            controls.append(instance)
    return controls
