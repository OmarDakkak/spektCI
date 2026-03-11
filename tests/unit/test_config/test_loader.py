"""Tests for configuration loader."""

from __future__ import annotations

import pytest

from spektci.config.loader import ConfigError, load_config
from spektci.config.schema import SpektciConfig


class TestConfigLoader:
    """Tests for the YAML config loader."""

    def test_loads_valid_config(self, tmp_path: object) -> None:
        from pathlib import Path
        config_path = Path(str(tmp_path)) / ".spektci.yaml"
        config_path.write_text(
            'version: "1"\n'
            "global:\n"
            "  threshold: 90\n"
            "  fail_on: warning\n"
            "controls:\n"
            "  image_tags:\n"
            "    enabled: true\n"
            "    forbidden_tags: [latest]\n"
        )
        config = load_config(config_path)
        assert isinstance(config, SpektciConfig)
        assert config.global_.threshold == 90
        assert config.global_.fail_on == "warning"
        assert config.controls.image_tags.forbidden_tags == ["latest"]

    def test_raises_on_missing_file(self) -> None:
        with pytest.raises(ConfigError, match="not found"):
            load_config("/nonexistent/.spektci.yaml")

    def test_raises_on_invalid_yaml(self, tmp_path: object) -> None:
        from pathlib import Path
        config_path = Path(str(tmp_path)) / ".spektci.yaml"
        config_path.write_text("{{invalid yaml")
        with pytest.raises(ConfigError, match="Invalid YAML"):
            load_config(config_path)

    def test_default_values(self, tmp_path: object) -> None:
        from pathlib import Path
        config_path = Path(str(tmp_path)) / ".spektci.yaml"
        config_path.write_text('version: "1"\n')
        config = load_config(config_path)
        assert config.global_.threshold == 80
        assert config.global_.output_format == "terminal"
        assert config.platform.type == "auto"
