"""Report formatters for analysis results."""

from __future__ import annotations

from spektci.reporters.base import BaseReporter
from spektci.reporters.json_reporter import JsonReporter
from spektci.reporters.sarif import SarifReporter
from spektci.reporters.terminal import TerminalReporter


def get_reporter(format_name: str) -> BaseReporter:
    """Get a reporter instance by format name.

    Args:
        format_name: One of 'terminal', 'json', 'sarif'.

    Returns:
        A reporter instance.

    Raises:
        ValueError: If the format is not supported.
    """
    reporters: dict[str, type[BaseReporter]] = {
        "terminal": TerminalReporter,
        "json": JsonReporter,
        "sarif": SarifReporter,
    }

    cls = reporters.get(format_name)
    if cls is None:
        raise ValueError(
            f"Unknown output format: {format_name!r}. "
            f"Supported formats: {', '.join(reporters)}"
        )
    return cls()
