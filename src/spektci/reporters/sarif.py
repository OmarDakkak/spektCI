"""SARIF v2.1.0 reporter — for GitHub Security tab, SonarQube, etc."""

from __future__ import annotations

import json

from spektci import __version__
from spektci.config.schema import SpektciConfig
from spektci.core.result import AnalysisResult, Severity
from spektci.reporters.base import BaseReporter

SARIF_SEVERITY_MAP = {
    Severity.ERROR: "error",
    Severity.WARNING: "warning",
    Severity.INFO: "note",
}


class SarifReporter(BaseReporter):
    """SARIF v2.1.0 report output."""

    def render(self, result: AnalysisResult, config: SpektciConfig) -> str:
        """Render the analysis result as SARIF v2.1.0 JSON."""
        rules: list[dict[str, object]] = []
        results: list[dict[str, object]] = []
        rule_ids_seen: set[str] = set()

        for cr in result.control_results:
            # Add rule definition if not seen
            if cr.control_id not in rule_ids_seen:
                rules.append({
                    "id": cr.control_id,
                    "name": cr.control_name.replace(" ", ""),
                    "shortDescription": {"text": cr.control_name},
                    "defaultConfiguration": {"level": "error"},
                })
                rule_ids_seen.add(cr.control_id)

            # Add findings as results
            for finding in cr.findings:
                sarif_result: dict[str, object] = {
                    "ruleId": finding.control_id,
                    "level": SARIF_SEVERITY_MAP.get(finding.severity, "note"),
                    "message": {"text": finding.message},
                }

                # Add location if available
                if finding.source_file:
                    location: dict[str, object] = {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": finding.source_file,
                                "uriBaseId": "%SRCROOT%",
                            },
                        }
                    }

                    if finding.source_line:
                        location["physicalLocation"]["region"] = {  # type: ignore[index]
                            "startLine": finding.source_line,
                        }

                    sarif_result["locations"] = [location]

                # Add remediation as fix description
                if finding.remediation:
                    sarif_result["fixes"] = [
                        {
                            "description": {"text": finding.remediation},
                        }
                    ]

                results.append(sarif_result)

        sarif_doc = {
            "$schema": "https://docs.oasis-open.org/sarif/sarif/v2.1.0/errata01/os/schemas/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "spektci",
                            "version": __version__,
                            "informationUri": "https://github.com/spektci/spektci",
                            "rules": rules,
                        }
                    },
                    "results": results,
                    "invocations": [
                        {
                            "executionSuccessful": True,
                            "properties": {
                                "platform": result.platform,
                                "project": result.project,
                                "branch": result.branch,
                                "complianceScore": round(result.compliance_score, 2),
                            },
                        }
                    ],
                }
            ],
        }

        return json.dumps(sarif_doc, indent=2, ensure_ascii=False)
