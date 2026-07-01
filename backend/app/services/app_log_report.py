import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class AppLogReportResponse(BaseModel):
    filename: str
    format: str
    content_type: str
    content: str


def build_app_log_report(
    evidence: dict[str, Any],
    findings: list[dict[str, Any]],
    report_format: str,
) -> AppLogReportResponse:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    source_file = str(evidence.get("source_file", "app-log"))
    stem = _safe_stem(source_file)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")

    if report_format == "json":
        content = _build_json_report(evidence, findings, generated_at)
        extension = "json"
        content_type = "application/json"
    elif report_format == "html":
        content = _build_html_report(evidence, findings, generated_at)
        extension = "html"
        content_type = "text/html; charset=utf-8"
    else:
        content = _build_markdown_report(evidence, findings, generated_at)
        extension = "md"
        content_type = "text/markdown; charset=utf-8"

    return AppLogReportResponse(
        filename=f"custosops_app_log_report_{stem}_{timestamp}.{extension}",
        format=report_format,
        content_type=content_type,
        content=content,
    )


def _build_json_report(evidence: dict[str, Any], findings: list[dict[str, Any]], generated_at: str) -> str:
    payload = {
        "report_type": "app_log",
        "generated_at": generated_at,
        "summary": _summary(evidence, findings),
        "evidence": evidence,
        "findings": findings,
        "limitations": [
            "This report is based on imported log evidence.",
            "A log sample may not represent the full incident window.",
            "No application, API, or infrastructure changes were made by CustosOps.",
            "Sensitive values should be redacted before sharing externally.",
        ],
    }

    return json.dumps(payload, indent=2)


def _build_markdown_report(evidence: dict[str, Any], findings: list[dict[str, Any]], generated_at: str) -> str:
    summary = _summary(evidence, findings)
    lines: list[str] = []

    lines.append("# CustosOps Application Log Evidence Report")
    lines.append("")
    lines.append(f"Generated: {generated_at}")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- Source file: `{summary['source_file']}`")
    lines.append(f"- Raw lines: `{summary['raw_line_count']}`")
    lines.append(f"- Parsed entries: `{summary['parsed_entry_count']}`")
    lines.append(f"- Findings: `{summary['finding_count']}`")
    lines.append(f"- Critical: `{summary['critical']}`")
    lines.append(f"- High: `{summary['high']}`")
    lines.append(f"- Medium: `{summary['medium']}`")
    lines.append(f"- Low: `{summary['low']}`")
    lines.append(f"- Info: `{summary['info']}`")
    lines.append("")

    if summary["sensitive_indicators"]:
        lines.append("## Sensitive Evidence Warning")
        lines.append("")
        lines.append("Potential sensitive-data indicators were detected:")
        lines.append("")

        for item in summary["sensitive_indicators"]:
            lines.append(f"- `{item}`")

        lines.append("")

    lines.append("## Top Recommended Actions")
    lines.append("")

    top_actions = _top_actions(findings)

    if top_actions:
        for action in top_actions:
            lines.append(f"- {action}")
    else:
        lines.append("- No app-log findings were generated from the imported evidence.")

    lines.append("")
    lines.append("## Findings")
    lines.append("")

    for finding in findings:
        lines.extend(_markdown_finding(finding))

    lines.append("## Report Limitations")
    lines.append("")
    lines.append("- This report is based on imported log evidence.")
    lines.append("- A log sample may not represent the full incident window.")
    lines.append("- No application, API, or infrastructure changes were made by CustosOps.")
    lines.append("- Sensitive values should be redacted before sharing externally.")

    return "\n".join(lines)


def _build_html_report(evidence: dict[str, Any], findings: list[dict[str, Any]], generated_at: str) -> str:
    markdown = _build_markdown_report(evidence, findings, generated_at)

    body = "\n".join(
        f"<p>{html.escape(line)}</p>" if line.strip() else "<br>"
        for line in markdown.splitlines()
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>CustosOps Application Log Evidence Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.45; color: #172033; }}
    p {{ margin: 0 0 8px; }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""


def _markdown_finding(finding: dict[str, Any]) -> list[str]:
    lines: list[str] = []

    lines.append(f"### {finding.get('title', 'Finding')}")
    lines.append("")
    lines.append(f"- Severity: `{finding.get('severity', 'unknown')}`")
    lines.append(f"- Confidence: `{finding.get('confidence', 'unknown')}`")
    lines.append(f"- Category: `{finding.get('category', 'unknown')}`")
    lines.append(f"- Affected asset: `{finding.get('affected_asset', 'unknown')}`")
    lines.append(f"- Finding ID: `{finding.get('finding_id', 'unknown')}`")
    lines.append("")
    lines.append("Why it matters:")
    lines.append("")
    lines.append(str(finding.get("why_it_matters", "")))
    lines.append("")
    lines.append("Evidence:")
    lines.append("")

    for item in finding.get("evidence", []):
        lines.append(f"- `{item.get('key', '')}`: `{item.get('value', '')}`")

    lines.append("")
    lines.append("Safe next steps:")
    lines.append("")

    for step in finding.get("safe_next_steps", []):
        lines.append(f"- {step}")

    lines.append("")
    lines.append("Limitations:")
    lines.append("")

    for limitation in finding.get("limitations", []):
        lines.append(f"- {limitation}")

    lines.append("")
    lines.append("Non-actions:")
    lines.append("")

    for non_action in finding.get("non_actions", []):
        lines.append(f"- {non_action}")

    lines.append("")

    return lines


def _summary(evidence: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, Any]:
    severities = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
    }

    for finding in findings:
        severity = finding.get("severity", "info")
        severities[severity] = severities.get(severity, 0) + 1

    return {
        "source_file": evidence.get("source_file", "unknown"),
        "raw_line_count": evidence.get("raw_line_count", 0),
        "parsed_entry_count": evidence.get("parsed_entry_count", 0),
        "finding_count": len(findings),
        "sensitive_indicators": evidence.get("sensitive_indicators", []),
        **severities,
    }


def _top_actions(findings: list[dict[str, Any]]) -> list[str]:
    actions: list[str] = []

    for finding in findings:
        steps = finding.get("safe_next_steps", [])

        if steps:
            actions.append(steps[0])

        if len(actions) >= 5:
            break

    return actions


def _safe_stem(filename: str) -> str:
    stem = Path(filename).stem or "app_log"
    cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in stem)
    return cleaned[:80] or "app_log"