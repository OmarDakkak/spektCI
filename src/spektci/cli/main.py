"""Click CLI group — main entry point for the spektci command."""

from __future__ import annotations

import logging
import sys

import click

from spektci import __version__
from spektci.cli.analyze import analyze
from spektci.cli.config_cmd import config


@click.group()
@click.version_option(version=__version__, prog_name="spektci")
@click.option("--verbose", is_flag=True, default=False, help="Enable debug output.")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """spektci — Multi-platform CI/CD compliance scanner."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(name)s %(levelname)s: %(message)s",
        stream=sys.stderr,
    )


cli.add_command(analyze)
cli.add_command(config)
