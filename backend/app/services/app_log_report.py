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



def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):
        return value.model_dump()

    if hasattr(value, "dict"):
        return value.dict()

    return {}

def build_app_log_report(
    evidence: dict[str, Any],
    findings: list[dict[str, Any]],
    report_format: str,
) -> AppLogReportResponse:
    evidence = _as_dict(evidence)
    findings = [_as_dict(finding) for finding in findings]
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    source_file = str(evidence.get("source_file", "app-log"))
    stem = _safe_stem(source_file)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    summary = _summary(evidence, findings)

    if report_format == "json":
        content = json.dumps(
            {
                "report_type": "app_log",
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

    return AppLogReportResponse(
        filename=f"custosops_app_log_report_{stem}_{timestamp}.{extension}",
        format=report_format,
        content_type=content_type,
        content=content,
    )


def _summary(evidence: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
    }

    for finding in findings:
        severity = _safe_severity(finding.get("severity", "info"))
        counts[severity] += 1

    return {
        "source_file": evidence.get("source_file", "app-log"),
        "raw_line_count": evidence.get("raw_line_count", 0),
        "parsed_entry_count": evidence.get("parsed_entry_count", 0),
        "finding_count": len(findings),
        "sensitive_indicators": evidence.get("sensitive_indicators", []),
        **counts,
    }


def _build_markdown_report(findings: list[dict[str, Any]], summary: dict[str, Any], generated_at: str) -> str:
    lines: list[str] = []

    lines.append("# CustosOps Application Log Evidence Report")
    lines.append("")
    lines.append(f"Generated: {generated_at}")
    lines.append(f"Source file: `{summary['source_file']}`")
    lines.append(f"Raw lines: `{summary['raw_line_count']}`")
    lines.append(f"Parsed entries: `{summary['parsed_entry_count']}`")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
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
        for item in summary["sensitive_indicators"]:
            lines.append(f"- `{item}`")
        lines.append("")

    lines.append("## Findings")
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
        lines.append("Limitations:")
        for limitation in finding.get("limitations", []):
            lines.append(f"- {limitation}")
        lines.append("")
        lines.append("Non-actions:")
        for non_action in finding.get("non_actions", []):
            lines.append(f"- {non_action}")
        lines.append("")

    lines.append("## Report Limitations")
    lines.append("")
    for limitation in _report_limitations():
        lines.append(f"- {limitation}")

    return "\n".join(lines)


def _build_html_report(findings: list[dict[str, Any]], summary: dict[str, Any], generated_at: str) -> str:
    cards = "\n".join(_html_finding(finding) for finding in findings)
    top_actions = "".join(
        f"<li>{html.escape(str(finding.get('safe_next_steps', [''])[0]))}</li>"
        for finding in findings
        if finding.get("safe_next_steps")
    )
    limitations = "".join(f"<li>{html.escape(item)}</li>" for item in _report_limitations())
    warning = ""

    if not top_actions:
        top_actions = "<li>No app-log findings were generated from the imported evidence.</li>"

    if summary["sensitive_indicators"]:
        indicators = "".join(f"<li><code>{html.escape(str(item))}</code></li>" for item in summary["sensitive_indicators"])
        warning = f"""
  <section class="card warning">
    <p class="eyebrow">Sensitive Evidence Warning</p>
    <p>Potential sensitive-data indicators were detected. Review and redact logs before sharing externally.</p>
    <ul>{indicators}</ul>
  </section>
"""

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>CustosOps Application Log Evidence Report</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  {_style()}
</head>
<body>
<main>
  <section class="hero">
    <p class="eyebrow">CustosOps Application Log Evidence Report</p>
    <h1>Application Log Evidence Report</h1>
    <p class="muted">Generated: {html.escape(generated_at)}</p>
    <p class="muted">Source file: {html.escape(str(summary['source_file']))}</p>
    <p class="muted">Raw lines: {summary['raw_line_count']} | Parsed entries: {summary['parsed_entry_count']}</p>
    <p class="muted">CustosOps analyzed imported log evidence locally and did not modify applications, APIs, services, or infrastructure.</p>
  </section>

  <section class="summary-grid">
    <div class="metric"><span>Findings</span><strong>{summary['finding_count']}</strong></div>
    <div class="metric"><span>Critical</span><strong>{summary['critical']}</strong></div>
    <div class="metric"><span>High</span><strong>{summary['high']}</strong></div>
    <div class="metric"><span>Medium</span><strong>{summary['medium']}</strong></div>
    <div class="metric"><span>Low</span><strong>{summary['low']}</strong></div>
    <div class="metric"><span>Info</span><strong>{summary['info']}</strong></div>
  </section>

  {warning}

  <section class="card">
    <p class="eyebrow">Top Recommended Actions</p>
    <ul>{top_actions}</ul>
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
    limitations = "".join(f"<li>{html.escape(str(item))}</li>" for item in finding.get("limitations", []))
    non_actions = "".join(f"<li>{html.escape(str(item))}</li>" for item in finding.get("non_actions", []))

    if not evidence:
        evidence = "<li>No evidence items provided.</li>"

    if not safe_steps:
        safe_steps = "<li>No safe next steps provided.</li>"

    if not limitations:
        limitations = "<li>No limitations provided.</li>"

    if not non_actions:
        non_actions = "<li>No non-actions provided.</li>"

    return f"""<section class="card">
  <div class="finding-top">
    <div>
      <p class="eyebrow">{html.escape(str(finding.get('category', 'Application evidence')))}</p>
      <h2>{html.escape(str(finding.get('title', 'Finding')))}</h2>
    </div>
    <span class="severity {severity}">{html.escape(severity)}</span>
  </div>

  <p class="muted">{html.escape(str(finding.get('why_it_matters', 'No explanation provided.')))}</p>

  <dl>
    <div><dt>Finding ID</dt><dd>{html.escape(str(finding.get('finding_id', 'unknown')))}</dd></div>
    <div><dt>Confidence</dt><dd>{html.escape(str(finding.get('confidence', 'unknown')))}</dd></div>
    <div><dt>Affected asset</dt><dd>{html.escape(str(finding.get('affected_asset', 'unknown')))}</dd></div>
    <div><dt>Status</dt><dd>open</dd></div>
  </dl>

  <h3>Evidence</h3>
  <ul>{evidence}</ul>

  <div class="columns">
    <div>
      <h3>Safe next steps</h3>
      <ul>{safe_steps}</ul>
    </div>
    <div>
      <h3>Limitations</h3>
      <ul>{limitations}</ul>
    </div>
  </div>

  <h3>Non-actions</h3>
  <ul>{non_actions}</ul>
</section>"""


def _safe_severity(value: Any) -> str:
    lowered = str(value).lower()

    if lowered in {"critical", "high", "medium", "low", "info"}:
        return lowered

    return "info"


def _report_limitations() -> list[str]:
    return [
        "This report is based on imported log evidence.",
        "A log sample may not represent the full incident window.",
        "No application, API, or infrastructure changes were made by CustosOps.",
        "Sensitive values should be redacted before sharing externally.",
    ]


def _safe_stem(filename: str) -> str:
    stem = Path(filename).stem or "app_log"
    cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in stem)
    return cleaned[:80] or "app_log"


def _style() -> str:
    return """<style>
    :root { font-family: Inter, Segoe UI, Arial, sans-serif; color: #0f172a; background: #f8fafc; }
    body { margin: 0; background: #f8fafc; }
    main { width: min(1120px, calc(100% - 32px)); margin: 0 auto; padding: 32px 0 48px; }
    .hero, .card { background: white; border: 1px solid #e2e8f0; border-radius: 18px; box-shadow: 0 12px 34px rgba(15, 23, 42, 0.08); }
    .hero { padding: 28px; margin-bottom: 18px; }
    .eyebrow { color: #2563eb; text-transform: uppercase; letter-spacing: 0.12em; font-size: 0.75rem; font-weight: 800; margin: 0 0 8px; }
    h1 { margin: 0 0 10px; font-size: clamp(2rem, 5vw, 3.6rem); letter-spacing: -0.06em; }
    .muted { color: #475569; line-height: 1.6; }
    .warning { border-color: #f59e0b; background: #fffbeb; }
    .summary-grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }
    .metric { background: #eff6ff; border: 1px solid #dbeafe; border-radius: 14px; padding: 14px; }
    .metric span { display: block; color: #475569; font-size: 0.82rem; margin-bottom: 4px; }
    .metric strong { font-size: 1.25rem; }
    .card { padding: 20px; margin-bottom: 14px; }
    .finding-top { display: flex; justify-content: space-between; gap: 12px; align-items: start; margin-bottom: 10px; }
    .severity { padding: 5px 9px; border-radius: 999px; text-transform: uppercase; font-size: 0.72rem; font-weight: 900; letter-spacing: 0.08em; }
    .critical, .high { background: #fee2e2; color: #991b1b; }
    .medium { background: #fef3c7; color: #92400e; }
    .low { background: #dcfce7; color: #166534; }
    .info { background: #dbeafe; color: #1e40af; }
    dl { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 14px 0; }
    dt { color: #64748b; font-size: 0.78rem; }
    dd { margin: 4px 0 0; font-weight: 800; word-break: break-word; }
    li { margin-bottom: 6px; line-height: 1.45; }
    code { background: #f1f5f9; border-radius: 6px; padding: 2px 5px; }
    .columns { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
    @media print { .card, .hero { box-shadow: none; } body { background: white; } }
    @media (max-width: 900px) { .summary-grid, .columns, dl { grid-template-columns: 1fr; } }
  </style>"""