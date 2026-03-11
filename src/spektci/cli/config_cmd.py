"""`spektci config` subcommands — init, view, validate."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from spektci.config.defaults import generate_default_config
from spektci.config.loader import ConfigError, load_config


@click.group()
def config() -> None:
    """Manage spektci configuration."""


@config.command()
@click.option("--output", "-o", default=".spektci.yaml", help="Output file path.")
@click.option("--force", "-f", is_flag=True, default=False, help="Overwrite existing file.")
@click.option(
    "--platform",
    type=click.Choice(["auto", "github", "jenkins", "bitbucket", "azure", "circleci"]),
    default="auto",
    help="Pre-configure for a specific platform.",
)
def init(output: str, force: bool, platform: str) -> None:
    """Generate a default .spektci.yaml configuration file."""
    output_path = Path(output)

    if output_path.exists() and not force:
        click.secho(
            f"File already exists: {output_path}. Use --force to overwrite.",
            fg="yellow",
            err=True,
        )
        sys.exit(1)

    content = generate_default_config()

    # If a specific platform was requested, patch the config
    if platform != "auto":
        content = content.replace("  type: auto", f"  type: {platform}")

    output_path.write_text(content, encoding="utf-8")
    click.secho(f"✓ Config written to {output_path}", fg="green")


@config.command()
@click.option("--config", "-c", "config_path", default=None, help="Path to configuration file.")
@click.option("--no-color", is_flag=True, default=False, help="Disable colorized output.")
def view(config_path: str | None, no_color: bool) -> None:
    """Display the effective configuration."""
    try:
        cfg = load_config(config_path)
    except ConfigError as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(2)

    # Render as YAML-like display
    import yaml
    from rich.console import Console
    from rich.syntax import Syntax

    data = cfg.model_dump(by_alias=True)
    yaml_str = yaml.dump(data, default_flow_style=False, sort_keys=False)

    if no_color:
        click.echo(yaml_str)
    else:
        console = Console()
        syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=False)
        console.print(syntax)


@config.command()
@click.option("--config", "-c", "config_path", default=None, help="Path to configuration file.")
def validate(config_path: str | None) -> None:
    """Validate a configuration file without running analysis."""
    try:
        load_config(config_path)
    except ConfigError as exc:
        click.secho(f"✗ Invalid configuration: {exc}", fg="red", err=True)
        sys.exit(2)

    click.secho("✓ Configuration is valid.", fg="green")
