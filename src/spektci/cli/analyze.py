"""`spektci analyze` command."""

from __future__ import annotations

import sys

import click

from spektci.adapters import get_adapter
from spektci.config.loader import ConfigError, load_config
from spektci.controls.registry import get_enabled_controls
from spektci.core.engine import AnalysisEngine
from spektci.core.result import Severity
from spektci.reporters import get_reporter


@click.command()
@click.option(
    "--platform",
    type=click.Choice(["auto", "github", "jenkins", "bitbucket", "azure", "circleci"]),
    default="auto",
    help="Target platform (auto-detected by default).",
)
@click.option("--repo", default=None, help="Repository path (e.g., owner/repo).")
@click.option("--branch", default=None, help="Branch to analyze.")
@click.option("--config", "config_path", default=None, help="Path to .spektci.yaml.")
@click.option("--threshold", type=int, default=None, help="Minimum compliance %% to pass (0-100).")
@click.option("--output", default=None, help="Write report to file.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["terminal", "json", "sarif"]),
    default=None,
    help="Output format.",
)
@click.option(
    "--controls",
    "controls_filter",
    default=None,
    help="Run only listed controls (comma-separated IDs, e.g. C001,C004).",
)
@click.option(
    "--skip-controls",
    "skip_controls",
    default=None,
    help="Skip listed controls (comma-separated IDs, e.g. C003,C008).",
)
@click.pass_context
def analyze(
    ctx: click.Context,
    platform: str,
    repo: str | None,
    branch: str | None,
    config_path: str | None,
    threshold: int | None,
    output: str | None,
    output_format: str | None,
    controls_filter: str | None,
    skip_controls: str | None,
) -> None:
    """Run compliance analysis on a CI/CD project."""
    # Load config
    try:
        config = load_config(config_path)
    except ConfigError as exc:
        click.secho(f"Configuration error: {exc}", fg="red", err=True)
        sys.exit(2)

    # Apply CLI overrides
    if platform != "auto":
        config.platform.type = platform  # type: ignore[assignment]
    if repo:
        config.platform.project = repo
    if branch:
        config.platform.branch = branch
    if threshold is not None:
        config.global_.threshold = threshold
    if output_format:
        config.global_.output_format = output_format  # type: ignore[assignment]
    if output:
        config.global_.output_file = output

    # Resolve adapter
    try:
        adapter = get_adapter(config)
    except Exception as exc:
        click.secho(f"Platform error: {exc}", fg="red", err=True)
        sys.exit(2)

    # Resolve controls
    controls = get_enabled_controls(config)

    # Apply --controls / --skip-controls CLI filters
    if controls_filter and skip_controls:
        click.secho(
            "Error: --controls and --skip-controls are mutually exclusive.",
            fg="red",
            err=True,
        )
        sys.exit(2)

    if controls_filter:
        include_ids = {c.strip().upper() for c in controls_filter.split(",")}
        controls = [c for c in controls if c.control_id in include_ids]

    if skip_controls:
        exclude_ids = {c.strip().upper() for c in skip_controls.split(",")}
        controls = [c for c in controls if c.control_id not in exclude_ids]

    # Run analysis
    engine = AnalysisEngine(adapter=adapter, controls=controls, config=config)
    try:
        result = engine.run()
    except Exception as exc:
        click.secho(f"Analysis error: {exc}", fg="red", err=True)
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)

    # Report
    reporter = get_reporter(config.global_.output_format)
    report_text = reporter.render(result, config)

    if config.global_.output_file:
        from pathlib import Path

        Path(config.global_.output_file).write_text(report_text, encoding="utf-8")
        click.echo(f"Report written to {config.global_.output_file}")
    else:
        click.echo(report_text)

    # Exit code
    effective_threshold = config.global_.threshold
    fail_severity = Severity.from_string(config.global_.fail_on)

    if not result.meets_threshold(effective_threshold):
        sys.exit(1)
    if result.has_severity_at_least(fail_severity):
        sys.exit(1)
