"""Terminal reporter — Rich-powered colorized output."""

from __future__ import annotations

from io import StringIO

from rich.console import Console
from rich.table import Table
from rich.text import Text

from spektci import __version__
from spektci.config.schema import SpektciConfig
from spektci.core.result import AnalysisResult, ControlStatus
from spektci.reporters.base import BaseReporter

STATUS_ICONS = {
    ControlStatus.PASS: ("✓", "green"),
    ControlStatus.FAIL: ("✗", "red"),
    ControlStatus.SKIP: ("⊘", "dim"),
    ControlStatus.ERROR: ("⚠", "yellow"),
}


class TerminalReporter(BaseReporter):
    """Rich-powered colorized terminal output."""

    def render(self, result: AnalysisResult, config: SpektciConfig) -> str:
        """Render the analysis result as a rich terminal report."""
        buf = StringIO()
        console = Console(file=buf, force_terminal=True, width=80)

        # Header
        console.print()
        console.print(
            f" [bold cyan]spektci[/bold cyan] v{__version__} — "
            f"CI/CD Compliance Scanner"
        )
        console.print()
        console.print(f" Platform: [bold]{result.platform.title()}[/bold]")
        console.print(
            f" Repo:     [bold]{result.project}[/bold] "
            f"(branch: {result.branch})"
        )
        console.print()

        # Control results
        for cr in result.control_results:
            icon, color = STATUS_ICONS.get(cr.status, ("?", "white"))
            status_label = "PASS" if cr.passed else cr.status.upper()

            line = Text()
            line.append(f" {icon} ", style=color)
            line.append(f"{cr.control_id}  ", style="bold")

            if cr.findings:
                # Show first finding message
                line.append(cr.findings[0].message, style=color)
            else:
                line.append(cr.control_name)

            # Right-align the status label
            padding = max(1, 72 - len(line.plain))
            line.append(" " * padding)
            line.append(status_label, style=f"bold {color}")

            console.print(line)

            # Show additional findings if any
            for finding in cr.findings[1:]:
                console.print(f"     └─ {finding.message}", style=color)

        # Summary
        console.print()
        console.print(" " + "─" * 56)
        score = result.compliance_score
        threshold = config.global_.threshold
        passing = result.passed_controls
        total = result.total_controls

        score_color = "green" if score >= threshold else "red"
        result_label = "PASS" if result.meets_threshold(threshold) else "FAIL"
        result_color = "green" if result_label == "PASS" else "red"

        console.print(
            f" Score: [{score_color}]{score:.1f}%[/{score_color}] "
            f"({passing}/{total} controls passing)    "
            f"Threshold: {threshold}%"
        )
        console.print(
            f" Result: [{result_color} bold]{result_label}[/{result_color} bold]"
        )
        console.print()

        return buf.getvalue()
