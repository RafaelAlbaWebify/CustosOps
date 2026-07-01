import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class DnsReportResponse(BaseModel):
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

def build_dns_report(
    evidence: dict[str, Any],
    findings: list[dict[str, Any]],
    report_format: str,
) -> DnsReportResponse:
    evidence = _as_dict(evidence)
    findings = [_as_dict(finding) for finding in findings]
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    summary = _summary(evidence, findings)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    stem = _safe_stem(summary["source_file"])

    if report_format == "json":
        content = _build_json_report(evidence, findings, summary, generated_at)
        extension = "json"
        content_type = "application/json"
    elif report_format == "html":
        content = _build_html_report(evidence, findings, summary, generated_at)
        extension = "html"
        content_type = "text/html; charset=utf-8"
    else:
        content = _build_markdown_report(evidence, findings, summary, generated_at)
        extension = "md"
        content_type = "text/markdown; charset=utf-8"

    return DnsReportResponse(
        filename=f"custosops_dns_report_{stem}_{timestamp}.{extension}",
        format=report_format,
        content_type=content_type,
        content=content,
    )


def _build_json_report(
    evidence: dict[str, Any],
    findings: list[dict[str, Any]],
    summary: dict[str, Any],
    generated_at: str,
) -> str:
    payload = {
        "report_type": "custosops.dns.v0.1",
        "generated_at": generated_at,
        "summary": summary,
        "evidence": evidence,
        "findings": findings,
        "limitations": _report_limitations(summary),
    }

    return json.dumps(payload, indent=2)


def _build_markdown_report(
    evidence: dict[str, Any],
    findings: list[dict[str, Any]],
    summary: dict[str, Any],
    generated_at: str,
) -> str:
    lines: list[str] = []

    lines.append("# CustosOps DNS Hygiene Report")
    lines.append("")
    lines.append(f"Generated: {generated_at}")
    lines.append(f"Source file: `{summary['source_file']}`")
    lines.append(f"Evidence source: `{summary['source_label']}`")
    lines.append(f"Record count: `{summary['record_count']}`")
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

    if summary["record_count_is_derived"]:
        lines.append("> Record count was derived from affected assets in loaded findings because raw DNS records were not available.")
        lines.append("")

    lines.append("## Top Recommended Actions")
    lines.append("")

    top_actions = _top_actions(findings)

    if top_actions:
        for action in top_actions:
            lines.append(f"- {action}")
    else:
        lines.append("- No DNS findings were generated from the evidence.")

    lines.append("")
    lines.append("## Findings")
    lines.append("")

    for finding in findings:
        lines.extend(_markdown_finding(finding))

    lines.append("## Report Limitations")
    lines.append("")

    for limitation in _report_limitations(summary):
        lines.append(f"- {limitation}")

    return "\n".join(lines)


def _build_html_report(
    evidence: dict[str, Any],
    findings: list[dict[str, Any]],
    summary: dict[str, Any],
    generated_at: str,
) -> str:
    cards = "\n".join(_html_finding(finding) for finding in findings)
    top_actions = "".join(f"<li>{html.escape(action)}</li>" for action in _top_actions(findings))
    limitations = "".join(f"<li>{html.escape(item)}</li>" for item in _report_limitations(summary))
    derived_note = ""

    if not top_actions:
        top_actions = "<li>No DNS findings were generated from the evidence.</li>"

    if summary["record_count_is_derived"]:
        derived_note = "<p class=\"notice\">Record count was derived from affected assets in loaded findings because raw DNS records were not available.</p>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>CustosOps DNS Hygiene Report</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  {_shared_style()}
</head>
<body>
<main>
  <section class="hero">
    <p class="eyebrow">CustosOps DNS Hygiene Report</p>
    <h1>DNS Hygiene Review</h1>
    <p class="muted">Generated: {html.escape(generated_at)}</p>
    <p class="muted">Source file: {html.escape(summary['source_file'])}</p>
    <p class="muted">Evidence source: {html.escape(summary['source_label'])}</p>
    <p class="muted">CustosOps did not modify DNS records.</p>
    {derived_note}
  </section>

  <section class="summary-grid six">
    <div class="metric"><span>Records</span><strong>{summary['record_count']}</strong></div>
    <div class="metric"><span>Findings</span><strong>{summary['finding_count']}</strong></div>
    <div class="metric"><span>Critical</span><strong>{summary['critical']}</strong></div>
    <div class="metric"><span>High</span><strong>{summary['high']}</strong></div>
    <div class="metric"><span>Medium</span><strong>{summary['medium']}</strong></div>
    <div class="metric"><span>Low</span><strong>{summary['low']}</strong></div>
  </section>

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

    return lines


def _html_finding(finding: dict[str, Any]) -> str:
    severity = _safe_severity(finding.get("severity", "info"))
    safe_steps = "".join(f"<li>{html.escape(str(step))}</li>" for step in finding.get("safe_next_steps", []))
    limitations = "".join(f"<li>{html.escape(str(item))}</li>" for item in finding.get("limitations", []))
    evidence = _html_evidence(finding)

    if not safe_steps:
        safe_steps = "<li>No safe next steps provided.</li>"

    if not limitations:
        limitations = "<li>No limitations provided.</li>"

    return f"""<section class="card">
  <div class="finding-top">
    <div>
      <p class="eyebrow">{html.escape(str(finding.get('category', 'DNS hygiene')))}</p>
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

  {evidence}

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
</section>"""


def _summary(evidence: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, Any]:
    severities = _severity_counts(findings)
    record_count, derived = _record_count(evidence, findings)

    return {
        "source_file": _source_file(evidence),
        "source_label": _source_label(evidence),
        "record_count": record_count,
        "record_count_is_derived": derived,
        "finding_count": len(findings),
        **severities,
    }


def _record_count(evidence: dict[str, Any], findings: list[dict[str, Any]]) -> tuple[int, bool]:
    for key in ["records", "dns_records", "items"]:
        value = evidence.get(key)

        if isinstance(value, list) and len(value) > 0:
            return len(value), False

    unique_assets = {str(finding.get("affected_asset")) for finding in findings if finding.get("affected_asset")}

    if unique_assets:
        return len(unique_assets), True

    for key in ["records", "dns_records", "items"]:
        value = evidence.get(key)

        if isinstance(value, list):
            return 0, False

    return 0, True


def _source_file(evidence: dict[str, Any]) -> str:
    source_file = evidence.get("source_file") or evidence.get("filename") or evidence.get("evidence_path")

    if source_file:
        return str(source_file)

    source_type = str(evidence.get("source_type", "")).lower()

    if "session" in source_type:
        return "restored-session-evidence"

    return "dns-evidence"


def _source_label(evidence: dict[str, Any]) -> str:
    source_type = str(evidence.get("source_type", "")).lower()
    generated_from = str(evidence.get("generated_from", "")).lower()
    source_file = evidence.get("source_file") or evidence.get("filename") or evidence.get("evidence_path")

    if "session" in source_type or "loaded findings" in generated_from:
        return "Restored session evidence"

    if "sample" in source_type or "sample" in str(source_file).lower():
        return "Sample evidence"

    if source_file:
        return f"Imported evidence: {source_file}"

    return "Loaded DNS evidence"


def _severity_counts(findings: list[dict[str, Any]]) -> dict[str, int]:
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

    return counts


def _safe_severity(value: Any) -> str:
    lowered = str(value).lower()

    if lowered in {"critical", "high", "medium", "low", "info"}:
        return lowered

    return "info"


def _top_actions(findings: list[dict[str, Any]]) -> list[str]:
    actions: list[str] = []

    for finding in findings:
        steps = finding.get("safe_next_steps", [])

        if steps:
            actions.append(f"{finding.get('title', 'Finding')}: {steps[0]}")

        if len(actions) >= 5:
            break

    return actions


def _report_limitations(summary: dict[str, Any]) -> list[str]:
    limitations = [
        "This report is based on imported or loaded DNS evidence.",
        "This is not a full DNS security assessment.",
        "DNS cleanup must be validated with service ownership and change control.",
        "No DNS records were modified by CustosOps.",
    ]

    if summary.get("record_count_is_derived"):
        limitations.append("Record count was derived from loaded findings because raw DNS records were not available.")

    return limitations


def _html_evidence(finding: dict[str, Any]) -> str:
    evidence = finding.get("evidence", [])

    if not evidence:
        return ""

    items = "".join(
        f"<li><code>{html.escape(str(item.get('key', 'evidence')))}</code>: {html.escape(str(item.get('value', '')))}</li>"
        for item in evidence
    )

    return f"<h3>Evidence</h3><ul>{items}</ul>"


def _safe_stem(value: str) -> str:
    stem = Path(str(value)).stem
    cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in stem)
    return cleaned[:80] or "dns_evidence"


def _shared_style() -> str:
    return """<style>
    :root { font-family: Inter, Segoe UI, Arial, sans-serif; color: #0f172a; background: #f8fafc; }
    body { margin: 0; background: #f8fafc; }
    main { width: min(1120px, calc(100% - 32px)); margin: 0 auto; padding: 32px 0 48px; }
    .hero, .card { background: white; border: 1px solid #e2e8f0; border-radius: 18px; box-shadow: 0 12px 34px rgba(15, 23, 42, 0.08); }
    .hero { padding: 28px; margin-bottom: 18px; }
    .eyebrow { color: #2563eb; text-transform: uppercase; letter-spacing: 0.12em; font-size: 0.75rem; font-weight: 800; margin: 0 0 8px; }
    h1 { margin: 0 0 10px; font-size: clamp(2rem, 5vw, 3.6rem); letter-spacing: -0.06em; }
    .muted { color: #475569; line-height: 1.6; }
    .notice { background: #fef3c7; color: #92400e; padding: 10px 12px; border-radius: 12px; font-weight: 700; }
    .summary-grid { display: grid; gap: 12px; margin: 18px 0; }
    .summary-grid.six { grid-template-columns: repeat(6, minmax(0, 1fr)); }
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