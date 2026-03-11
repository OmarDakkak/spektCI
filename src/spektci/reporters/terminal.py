"""Terminal reporter — Rich-powered colorized output."""

from __future__ import annotations

import os
from io import StringIO
from typing import TYPE_CHECKING

from rich.console import Console
from rich.text import Text

from spektci import __version__
from spektci.core.result import AnalysisResult, ControlStatus
from spektci.reporters.base import BaseReporter

if TYPE_CHECKING:
    from spektci.config.schema import SpektciConfig

STATUS_ICONS: dict[str, tuple[str, str]] = {
    ControlStatus.PASS: ("✓", "green"),
    ControlStatus.FAIL: ("✗", "red"),
    ControlStatus.SKIP: ("⊘", "dim"),
    ControlStatus.ERROR: ("⚠", "yellow"),
}


def _detect_width() -> int:
    """Auto-detect terminal width, defaulting to 100."""
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 100


class TerminalReporter(BaseReporter):
    """Rich-powered colorized terminal output."""

    def render(self, result: AnalysisResult, config: SpektciConfig) -> str:
        """Render the analysis result as a rich terminal report."""
        width = _detect_width()
        buf = StringIO()
        console = Console(file=buf, force_terminal=True, width=width)

        # Header / Banner
        console.print()
        console.print(f" [bold cyan]spektci[/bold cyan] v{__version__} — CI/CD Compliance Scanner")
        console.rule(style="dim")
        console.print(f" Platform: [bold]{result.platform.title()}[/bold]")
        console.print(f" Repo:     [bold]{result.project}[/bold] (branch: {result.branch})")
        console.print()

        # Control results
        for cr in result.control_results:
            icon, color = STATUS_ICONS.get(cr.status, ("?", "white"))
            status_label = "PASS" if cr.passed else cr.status.upper()

            line = Text()
            line.append(f" {icon} ", style=color)
            line.append(f"{cr.control_id}  ", style="bold")
            line.append(cr.control_name)

            # Right-align the status label
            padding = max(1, width - 8 - len(line.plain))
            line.append(" " * padding)
            line.append(status_label, style=f"bold {color}")

            console.print(line)

            # Show findings with location info
            for finding in cr.findings:
                loc = ""
                if finding.source_file:
                    loc = f"[dim]{finding.source_file}"
                    if finding.source_line:
                        loc += f":{finding.source_line}"
                    loc += "[/dim] "

                console.print(
                    f"     └─ {loc}{finding.message}",
                    style=color,
                )

        # Summary
        console.print()
        console.rule(style="dim")
        score = result.compliance_score
        threshold = config.global_.threshold
        passing = result.passed_controls
        total = result.total_controls

        score_color = "green" if score >= threshold else "red"
        result_label = "PASS" if result.meets_threshold(threshold) else "FAIL"
        result_color = "green" if result_label == "PASS" else "red"

        # Compliance bar
        bar_width = min(40, width - 30)
        filled = int(bar_width * score / 100) if bar_width > 0 else 0
        bar = "█" * filled + "░" * (bar_width - filled)
        console.print(f" [{score_color}]{bar}[/{score_color}]  {score:.1f}%")
        console.print()
        console.print(
            f" Score: [{score_color}]{score:.1f}%[/{score_color}] "
            f"({passing}/{total} controls passing)    "
            f"Threshold: {threshold}%"
        )
        console.print(f" Result: [{result_color} bold]{result_label}[/{result_color} bold]")
        console.print()

        return buf.getvalue()
