import html
import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel


class RiskySignInReportResponse(BaseModel):
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


def _safe_stem(value: str) -> str:
    safe = "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
    return safe or "risky-signins"


def build_risky_signin_report(
    evidence: dict[str, Any],
    findings: list[dict[str, Any]],
    report_format: str,
) -> RiskySignInReportResponse:
    evidence = _as_dict(evidence)
    findings = [_as_dict(finding) for finding in findings]
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    summary = _summary(evidence, findings)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")

    if report_format == "json":
        content = _build_json_report(evidence, findings, summary, generated_at)
        extension = "json"
        content_type = "application/json"
    elif report_format == "markdown":
        content = _build_markdown_report(evidence, findings, summary, generated_at)
        extension = "md"
        content_type = "text/markdown; charset=utf-8"
    else:
        content = _build_html_report(evidence, findings, summary, generated_at)
        extension = "html"
        content_type = "text/html; charset=utf-8"

    return RiskySignInReportResponse(
        filename=f"custosops_risky_signin_report_{_safe_stem(summary['tenant_label'])}_{timestamp}.{extension}",
        format=report_format,
        content_type=content_type,
        content=content,
    )


def _summary(evidence: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(finding.get("severity", "info")) for finding in findings)
    records = evidence.get("records") or []
    risky_successes = [
        record
        for record in records
        if str(record.get("status", "")).lower() == "success"
        and str(record.get("risk_level_aggregated", "")).lower() in {"medium", "high"}
    ]
    users = sorted({str(record.get("user_principal_name", "unknown")) for record in records})

    return {
        "tenant_label": evidence.get("tenant_label") or "synthetic-tenant",
        "source_file": evidence.get("source_file") or "unknown-source",
        "record_count": evidence.get("parsed_record_count") or len(records),
        "user_count": len(users),
        "risky_success_count": len(risky_successes),
        "finding_count": len(findings),
        "critical": counts.get("critical", 0),
        "high": counts.get("high", 0),
        "medium": counts.get("medium", 0),
        "low": counts.get("low", 0),
        "info": counts.get("info", 0),
    }


def _build_json_report(
    evidence: dict[str, Any],
    findings: list[dict[str, Any]],
    summary: dict[str, Any],
    generated_at: str,
) -> str:
    return json.dumps(
        {
            "report_type": "custosops.risky_signins.v0.1",
            "generated_at": generated_at,
            "summary": summary,
            "evidence": evidence,
            "findings": findings,
            "limitations": _report_limitations(),
        },
        indent=2,
    )


def _build_markdown_report(
    evidence: dict[str, Any],
    findings: list[dict[str, Any]],
    summary: dict[str, Any],
    generated_at: str,
) -> str:
    lines: list[str] = []
    lines.append("# CustosOps Risky Sign-In Evidence Report")
    lines.append("")
    lines.append(f"Generated: {generated_at}")
    lines.append(f"Tenant label: `{summary['tenant_label']}`")
    lines.append(f"Evidence source: `{summary['source_file']}`")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- Sign-in records reviewed: `{summary['record_count']}`")
    lines.append(f"- Users represented: `{summary['user_count']}`")
    lines.append(f"- Risky successful sign-ins: `{summary['risky_success_count']}`")
    lines.append(f"- Total findings: `{summary['finding_count']}`")
    lines.append(f"- High: `{summary['high']}`")
    lines.append(f"- Medium: `{summary['medium']}`")
    lines.append(f"- Info: `{summary['info']}`")
    lines.append("")
    lines.append("## Top Recommended Actions")
    lines.append("")
    top_actions = _top_actions(findings)
    if top_actions:
        for action in top_actions:
            lines.append(f"- {action}")
    else:
        lines.append("- No risky sign-in findings were generated from the evidence.")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    for finding in findings:
        lines.extend(_markdown_finding(finding))
    lines.append("## Report Limitations")
    lines.append("")
    for limitation in _report_limitations():
        lines.append(f"- {limitation}")
    return "\n".join(lines)


def _build_html_report(
    evidence: dict[str, Any],
    findings: list[dict[str, Any]],
    summary: dict[str, Any],
    generated_at: str,
) -> str:
    top_actions = "".join(f"<li>{html.escape(action)}</li>" for action in _top_actions(findings))
    if not top_actions:
        top_actions = "<li>No risky sign-in findings were generated from the evidence.</li>"
    cards = "\n".join(_html_finding(finding) for finding in findings)
    limitations = "".join(f"<li>{html.escape(item)}</li>" for item in _report_limitations())

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>CustosOps Risky Sign-In Evidence Report - {html.escape(summary['tenant_label'])}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  {_shared_style()}
</head>
<body>
<main>
  <section class="hero">
    <p class="eyebrow">CustosOps Risky Sign-In Evidence Report</p>
    <h1>{html.escape(summary['tenant_label'])}</h1>
    <p class="muted">Generated: {html.escape(generated_at)}</p>
    <p class="muted">Evidence source: {html.escape(summary['source_file'])}</p>
    <p class="muted">Read-only identity evidence review. No live tenant action was performed.</p>
  </section>

  <section class="summary-grid five">
    <div class="metric"><span>Records</span><strong>{summary['record_count']}</strong></div>
    <div class="metric"><span>Users</span><strong>{summary['user_count']}</strong></div>
    <div class="metric"><span>Risky Success</span><strong>{summary['risky_success_count']}</strong></div>
    <div class="metric"><span>High</span><strong>{summary['high']}</strong></div>
    <div class="metric"><span>Medium</span><strong>{summary['medium']}</strong></div>
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
    safe_steps = "".join(f"<li>{html.escape(str(step))}</li>" for step in finding.get("safe_next_steps", []))
    limitations = "".join(f"<li>{html.escape(str(item))}</li>" for item in finding.get("limitations", []))
    return f"""
  <section class="card finding">
    <p class="eyebrow">{html.escape(str(finding.get('severity', 'info')).upper())} / {html.escape(str(finding.get('category', 'unknown')))}</p>
    <h2>{html.escape(str(finding.get('title', 'Finding')))}</h2>
    <p class="muted">Finding ID: {html.escape(str(finding.get('finding_id', 'unknown')))} | Affected asset: {html.escape(str(finding.get('affected_asset', 'unknown')))}</p>
    <p>{html.escape(str(finding.get('why_it_matters', '')))}</p>
    <h3>Safe next steps</h3>
    <ul>{safe_steps}</ul>
    <h3>Limitations</h3>
    <ul>{limitations}</ul>
  </section>
"""


def _top_actions(findings: list[dict[str, Any]]) -> list[str]:
    actions: list[str] = []
    for finding in findings:
        for step in finding.get("safe_next_steps", []):
            if step not in actions:
                actions.append(str(step))
            if len(actions) >= 5:
                return actions
    return actions


def _report_limitations() -> list[str]:
    return [
        "CustosOps reviews local, imported, or synthetic sign-in evidence only; it does not query a live Microsoft tenant.",
        "Findings support triage and escalation; they are not proof of account compromise by themselves.",
        "Identity actions such as password reset, session revocation, account disablement, or Conditional Access changes must be performed in approved admin tools with authorization.",
        "Geolocation, risk levels, MFA fields, and client app labels depend on source data quality.",
    ]


def _shared_style() -> str:
    return """
  <style>
    :root { color-scheme: dark; font-family: Inter, Segoe UI, Arial, sans-serif; }
    body { margin: 0; background: #0f172a; color: #e5eefb; }
    main { max-width: 1120px; margin: 0 auto; padding: 32px; }
    .hero, .card { background: #111c33; border: 1px solid #263854; border-radius: 20px; padding: 24px; margin-bottom: 20px; box-shadow: 0 18px 42px rgba(0,0,0,.24); }
    .eyebrow { margin: 0 0 8px; color: #7dd3fc; font-size: 12px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
    h1, h2, h3 { margin-top: 0; }
    .muted { color: #9fb2cc; }
    .summary-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 14px; margin-bottom: 20px; }
    .metric { background: #0b1224; border: 1px solid #263854; border-radius: 16px; padding: 16px; }
    .metric span { display: block; color: #9fb2cc; font-size: 12px; }
    .metric strong { display: block; margin-top: 8px; font-size: 28px; }
    li { margin: 6px 0; }
    @media (max-width: 800px) { .summary-grid { grid-template-columns: 1fr 1fr; } main { padding: 18px; } }
  </style>
"""
