"""JSON reporter — structured JSON output."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from spektci.reporters.base import BaseReporter

if TYPE_CHECKING:
    from spektci.config.schema import SpektciConfig
    from spektci.core.result import AnalysisResult


class JsonReporter(BaseReporter):
    """JSON report output."""

    def render(self, result: AnalysisResult, config: SpektciConfig) -> str:
        """Render the analysis result as a JSON string."""
        report = {
            "version": "1",
            "platform": result.platform,
            "project": result.project,
            "branch": result.branch,
            "compliance_score": round(result.compliance_score, 2),
            "threshold": config.global_.threshold,
            "result": "pass" if result.meets_threshold(config.global_.threshold) else "fail",
            "summary": {
                "total_controls": result.total_controls,
                "passed": result.passed_controls,
                "failed": result.failed_controls,
                "total_findings": len(result.all_findings),
            },
            "controls": [
                {
                    "id": cr.control_id,
                    "name": cr.control_name,
                    "status": cr.status,
                    "findings": [
                        {
                            "severity": str(f.severity),
                            "message": f.message,
                            "source_file": f.source_file or None,
                            "source_line": f.source_line or None,
                            "remediation": f.remediation or None,
                        }
                        for f in cr.findings
                    ],
                }
                for cr in result.control_results
            ],
        }

        return json.dumps(report, indent=2, ensure_ascii=False)
