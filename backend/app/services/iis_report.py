import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class IisReportResponse(BaseModel):
    filename: str
    format: str
    content_type: str
    content: str


def build_iis_report(
    evidence: dict[str, Any],
    findings: list[dict[str, Any]],
    report_format: str,
) -> IisReportResponse:
    evidence = _as_dict(evidence)
    findings = [_as_dict(finding) for finding in findings]

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    source_file = str(evidence.get("source_file", "iis-application"))
    stem = _safe_stem(source_file)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    summary = _summary(evidence, findings)

    if report_format == "json":
        content = json.dumps(
            {
                "report_type": "custosops.iis_application.v0.1",
                "generated_at": generated_at,
                "summary": summary,
                "evidence": evidence,
                "findings": findings,
                "limitations": _report_limitations(),
            },
            indent=2,
        )
        extension = "json"
        content_type = "application/json"
    elif report_format == "html":
        content = _build_html_report(findings, summary, generated_at)
        extension = "html"
        content_type = "text/html; charset=utf-8"
    else:
        content = _build_markdown_report(findings, summary, generated_at)
        extension = "md"
        content_type = "text/markdown; charset=utf-8"

    return IisReportResponse(
        filename=f"custosops_iis_application_report_{stem}_{timestamp}.{extension}",
        format=report_format,
        content_type=content_type,
        content=content,
    )


def _summary(evidence: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

    for finding in findings:
        severity = _safe_severity(finding.get("severity", "info"))
        counts[severity] += 1

    return {
        "source_file": evidence.get("source_file", "iis-application"),
        "asset": evidence.get("asset", "unknown"),
        "iis_detected": bool(evidence.get("iis_detected", False)),
        "appcmd_available": bool(evidence.get("appcmd_available", False)),
        "service_count": len(evidence.get("services", []) or []),
        "site_count": len(evidence.get("sites", []) or []),
        "application_pool_count": len(evidence.get("application_pools", []) or []),
        "application_count": len(evidence.get("applications", []) or []),
        "log_file_count": len(evidence.get("log_files", []) or []),
        "finding_count": len(findings),
        **counts,
    }


def _build_markdown_report(findings: list[dict[str, Any]], summary: dict[str, Any], generated_at: str) -> str:
    lines: list[str] = []

    lines.append("# CustosOps IIS/Application Evidence Report")
    lines.append("")
    lines.append(f"Generated: {generated_at}")
    lines.append(f"Source file: `{summary['source_file']}`")
    lines.append(f"Asset: `{summary['asset']}`")
    lines.append(f"IIS detected: `{summary['iis_detected']}`")
    lines.append(f"appcmd available: `{summary['appcmd_available']}`")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- Services: `{summary['service_count']}`")
    lines.append(f"- Sites: `{summary['site_count']}`")
    lines.append(f"- Application pools: `{summary['application_pool_count']}`")
    lines.append(f"- Applications: `{summary['application_count']}`")
    lines.append(f"- Log files: `{summary['log_file_count']}`")
    lines.append(f"- Findings: `{summary['finding_count']}`")
    lines.append("")

    lines.append("## Findings")
    lines.append("")

    if not findings:
        lines.append("No IIS/Application findings were detected from the provided evidence.")
        lines.append("")

    for finding in findings:
        lines.append(f"### {finding.get('title', 'Finding')}")
        lines.append("")
        lines.append(f"- Severity: `{finding.get('severity', 'unknown')}`")
        lines.append(f"- Confidence: `{finding.get('confidence', 'unknown')}`")
        lines.append(f"- Category: `{finding.get('category', 'unknown')}`")
        lines.append(f"- Affected asset: `{finding.get('affected_asset', 'unknown')}`")
        lines.append(f"- Finding ID: `{finding.get('finding_id', 'unknown')}`")
        lines.append("")
        lines.append(str(finding.get("why_it_matters", "")))
        lines.append("")
        lines.append("Evidence:")
        for item in finding.get("evidence", []):
            lines.append(f"- `{item.get('key', '')}`: `{item.get('value', '')}`")
        lines.append("")
        lines.append("Safe next steps:")
        for step in finding.get("safe_next_steps", []):
            lines.append(f"- {step}")
        lines.append("")

    lines.append("## Report Limitations")
    lines.append("")
    for limitation in _report_limitations():
        lines.append(f"- {limitation}")

    return "\n".join(lines)


def _build_html_report(findings: list[dict[str, Any]], summary: dict[str, Any], generated_at: str) -> str:
    cards = "\n".join(_html_finding(finding) for finding in findings)
    if not cards:
        cards = '<section class="card"><p>No IIS/Application findings were detected from the provided evidence.</p></section>'

    limitations = "".join(f"<li>{html.escape(item)}</li>" for item in _report_limitations())

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>CustosOps IIS/Application Evidence Report</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  {_style()}
</head>
<body>
<main>
  <section class="hero">
    <p class="eyebrow">CustosOps IIS/Application Evidence Report</p>
    <h1>IIS/Application Evidence Report</h1>
    <p class="muted">Generated: {html.escape(generated_at)}</p>
    <p class="muted">Source file: {html.escape(str(summary['source_file']))}</p>
    <p class="muted">Asset: {html.escape(str(summary['asset']))}</p>
    <p class="muted">IIS detected: {summary['iis_detected']} | appcmd available: {summary['appcmd_available']}</p>
    <p class="muted">CustosOps collected IIS/Application evidence locally in read-only mode.</p>
  </section>

  <section class="summary-grid">
    <div class="metric"><span>Services</span><strong>{summary['service_count']}</strong></div>
    <div class="metric"><span>Sites</span><strong>{summary['site_count']}</strong></div>
    <div class="metric"><span>App pools</span><strong>{summary['application_pool_count']}</strong></div>
    <div class="metric"><span>Findings</span><strong>{summary['finding_count']}</strong></div>
  </section>

  {cards}

  <section class="card">
    <p class="eyebrow">Report Limitations</p>
    <ul>{limitations}</ul>
  </section>
</main>
</body>
</html>
"""


def _html_finding(finding: dict[str, Any]) -> str:
    severity = _safe_severity(finding.get("severity", "info"))
    evidence = "".join(
        f"<li><code>{html.escape(str(item.get('key', 'evidence')))}</code>: {html.escape(str(item.get('value', '')))}</li>"
        for item in finding.get("evidence", [])
    )
    safe_steps = "".join(f"<li>{html.escape(str(item))}</li>" for item in finding.get("safe_next_steps", []))

    if not evidence:
        evidence = "<li>No evidence items provided.</li>"
    if not safe_steps:
        safe_steps = "<li>No safe next steps provided.</li>"

    return f"""<section class="card">
  <div class="finding-top">
    <div>
      <p class="eyebrow">{html.escape(str(finding.get('category', 'IIS/Application evidence')))}</p>
      <h2>{html.escape(str(finding.get('title', 'Finding')))}</h2>
    </div>
    <span class="severity {severity}">{html.escape(severity)}</span>
  </div>

  <p class="muted">{html.escape(str(finding.get('why_it_matters', 'No explanation provided.')))}</p>

  <dl>
    <div><dt>Finding ID</dt><dd>{html.escape(str(finding.get('finding_id', 'unknown')))}</dd></div>
    <div><dt>Confidence</dt><dd>{html.escape(str(finding.get('confidence', 'unknown')))}</dd></div>
    <div><dt>Affected asset</dt><dd>{html.escape(str(finding.get('affected_asset', 'unknown')))}</dd></div>
  </dl>

  <h3>Evidence</h3>
  <ul>{evidence}</ul>

  <h3>Safe next steps</h3>
  <ul>{safe_steps}</ul>
</section>
"""


def _report_limitations() -> list[str]:
    return [
        "IIS/Application evidence is read-only and does not modify local services, sites, application pools, or logging configuration.",
        "appcmd inventory is available only when IIS management tooling is installed and accessible.",
        "No IIS installed or no IIS logs present is a valid collection state and should be interpreted with host role context.",
        "Findings should be correlated with Windows Event and Application Log evidence before operational action.",
    ]


def _safe_severity(value: object) -> str:
    severity = str(value).lower()
    if severity in {"critical", "high", "medium", "low", "info"}:
        return severity
    return "info"


def _safe_stem(source_file: str) -> str:
    stem = Path(source_file).stem or "iis-application"
    cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in stem)
    return cleaned.strip("_")[:80] or "iis-application"


def _as_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    return dict(value)


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: Inter, Segoe UI, Arial, sans-serif; background: #f4f7fb; color: #172033; }
body { margin: 0; background: #f4f7fb; }
main { max-width: 1120px; margin: 0 auto; padding: 32px; }
.hero, .card { background: #fff; border: 1px solid #d8e0ec; border-radius: 18px; padding: 24px; margin-bottom: 18px; box-shadow: 0 14px 40px rgba(27, 39, 64, .08); }
.eyebrow { text-transform: uppercase; letter-spacing: .08em; font-size: 12px; color: #55708f; font-weight: 700; }
.muted { color: #5e6f84; }
.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-bottom: 18px; }
.metric { background: #fff; border: 1px solid #d8e0ec; border-radius: 14px; padding: 18px; }
.metric span { color: #5e6f84; display: block; font-size: 13px; }
.metric strong { font-size: 28px; }
.finding-top { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
.severity { padding: 6px 10px; border-radius: 999px; background: #e9eef7; font-weight: 700; }
.severity.high, .severity.critical { background: #ffe5e5; color: #9b1c1c; }
.severity.medium { background: #fff4d8; color: #8a5a00; }
.severity.low { background: #e7f5ff; color: #0b5f8a; }
dl { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
dt { color: #5e6f84; font-size: 12px; }
dd { margin: 0; font-weight: 700; }
code { background: #eef3fa; padding: 2px 5px; border-radius: 6px; }
</style>"""