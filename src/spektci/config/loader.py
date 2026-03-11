"""YAML config loader with validation."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from spektci.config.schema import SpektciConfig

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_FILENAME = ".spektci.yaml"


class ConfigError(Exception):
    """Raised when configuration is invalid or cannot be loaded."""


def load_config(path: str | Path | None = None) -> SpektciConfig:
    """Load and validate a .spektci.yaml configuration file.

    Args:
        path: Path to the config file. If None, searches for .spektci.yaml
              in the current directory and parent directories.

    Returns:
        Validated SpektciConfig instance.

    Raises:
        ConfigError: If the file cannot be found, read, or validated.
    """
    config_path = _resolve_config_path(path)

    logger.info("Loading config from: %s", config_path)
    try:
        raw = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"Cannot read config file: {config_path}") from exc

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {config_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError(f"Config file must be a YAML mapping, got {type(data).__name__}")

    try:
        config = SpektciConfig.model_validate(data)
    except Exception as exc:
        raise ConfigError(f"Config validation error: {exc}") from exc

    logger.debug("Config loaded successfully: version=%s", config.version)
    return config


def _resolve_config_path(path: str | Path | None) -> Path:
    """Resolve the config file path, searching upward if not specified."""
    if path is not None:
        resolved = Path(path)
        if not resolved.exists():
            raise ConfigError(f"Config file not found: {resolved}")
        return resolved

    # Search current directory and parents
    current = Path.cwd()
    for directory in [current, *current.parents]:
        candidate = directory / DEFAULT_CONFIG_FILENAME
        if candidate.exists():
            return candidate

    raise ConfigError(
        f"No {DEFAULT_CONFIG_FILENAME} found in current directory or parent directories. "
        f"Run 'spektci config init' to create one."
    )
