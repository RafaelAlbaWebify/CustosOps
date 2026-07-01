import html
import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel


SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}

REVIEW_STATUSES = {
    "open",
    "reviewed",
    "needs_follow_up",
    "accepted_risk",
    "false_positive",
    "verify",
    "accepted",
    "fixed",
    "not_applicable",
}


class ExecutiveSummaryReportResponse(BaseModel):
    filename: str
    format: str
    content_type: str
    content: str


def build_executive_summary_report(
    modules: list[dict[str, Any]],
    report_format: str,
) -> ExecutiveSummaryReportResponse:
    modules = [_normalize_module(module) for module in modules]
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")

    summary = _build_summary(modules)

    if report_format == "json":
        content = json.dumps(
            {
                "report_type": "custosops.executive_summary.v0.1",
                "generated_at": generated_at,
                "summary": summary,
                "modules": modules,
                "top_risks": _top_risks(modules),
                "recommended_actions": _recommended_actions(modules),
                "limitations": _report_limitations(),
            },
            indent=2,
        )
        extension = "json"
        content_type = "application/json"
    elif report_format == "html":
        content = _build_html_report(modules, summary, generated_at)
        extension = "html"
        content_type = "text/html; charset=utf-8"
    else:
        content = _build_markdown_report(modules, summary, generated_at)
        extension = "md"
        content_type = "text/markdown; charset=utf-8"

    return ExecutiveSummaryReportResponse(
        filename=f"custosops_executive_summary_{timestamp}.{extension}",
        format=report_format,
        content_type=content_type,
        content=content,
    )


def _normalize_module(module: dict[str, Any]) -> dict[str, Any]:
    module_id = str(module.get("module_id") or module.get("id") or "unknown")
    module_name = str(module.get("module_name") or module.get("name") or module_id)
    source = str(module.get("source") or module.get("source_file") or "loaded evidence")
    evidence = _as_dict(module.get("evidence", {}))
    findings = [_as_dict(finding) for finding in module.get("findings", [])]

    return {
        "module_id": module_id,
        "module_name": module_name,
        "source": source,
        "evidence": evidence,
        "findings": findings,
        "summary": _module_summary(module_id, module_name, source, evidence, findings),
    }


def _module_summary(
    module_id: str,
    module_name: str,
    source: str,
    evidence: dict[str, Any],
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    counts = _severity_counts(findings)
    review_counts = _review_counts(findings)

    return {
        "module_id": module_id,
        "module_name": module_name,
        "source": source,
        "finding_count": len(findings),
        "severity_counts": counts,
        "review_counts": review_counts,
        "evidence_size": _evidence_size(module_id, evidence),
    }


def _build_summary(modules: list[dict[str, Any]]) -> dict[str, Any]:
    all_findings = _all_findings(modules)
    severity_counts = _severity_counts(all_findings)
    review_counts = _review_counts(all_findings)

    return {
        "module_count": len(modules),
        "finding_count": len(all_findings),
        "severity_counts": severity_counts,
        "review_counts": review_counts,
        "module_summaries": [module["summary"] for module in modules],
    }


def _severity_counts(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
    }

    for finding in findings:
        severity = _safe_severity(finding.get("severity"))
        counts[severity] += 1

    return counts


def _review_counts(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "open": 0,
        "reviewed": 0,
        "needs_follow_up": 0,
        "accepted_risk": 0,
        "false_positive": 0,
        "other": 0,
    }

    for finding in findings:
        status = str(finding.get("status") or "open")

        if status in counts:
            counts[status] += 1
        elif status in REVIEW_STATUSES:
            counts["other"] += 1
        else:
            counts["open"] += 1

    return counts


def _top_risks(modules: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []

    for module in modules:
        for finding in module["findings"]:
            risks.append(
                {
                    "module_id": module["module_id"],
                    "module_name": module["module_name"],
                    "finding_id": finding.get("finding_id", "unknown"),
                    "title": finding.get("title", "Finding"),
                    "severity": _safe_severity(finding.get("severity")),
                    "affected_asset": finding.get("affected_asset", "unknown"),
                    "status": finding.get("status", "open"),
                    "review_notes": finding.get("review_notes"),
                }
            )

    return sorted(
        risks,
        key=lambda risk: (
            SEVERITY_ORDER.get(str(risk["severity"]), 9),
            str(risk["module_name"]),
            str(risk["title"]),
        ),
    )[:limit]


def _recommended_actions(modules: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    for module in modules:
        for finding in module["findings"]:
            steps = finding.get("safe_next_steps") or []

            if not steps:
                continue

            actions.append(
                {
                    "module_name": module["module_name"],
                    "finding_id": finding.get("finding_id", "unknown"),
                    "severity": _safe_severity(finding.get("severity")),
                    "title": finding.get("title", "Finding"),
                    "action": str(steps[0]),
                }
            )

    return sorted(
        actions,
        key=lambda action: (
            SEVERITY_ORDER.get(str(action["severity"]), 9),
            str(action["module_name"]),
            str(action["title"]),
        ),
    )[:limit]


def _build_markdown_report(modules: list[dict[str, Any]], summary: dict[str, Any], generated_at: str) -> str:
    top_risks = _top_risks(modules)
    actions = _recommended_actions(modules)

    lines: list[str] = []

    lines.append("# CustosOps Executive Summary Pack")
    lines.append("")
    lines.append(f"Generated: {generated_at}")
    lines.append("")
    lines.append("## Portfolio Summary")
    lines.append("")
    lines.append(f"- Modules included: `{summary['module_count']}`")
    lines.append(f"- Total findings: `{summary['finding_count']}`")
    lines.append(f"- Critical: `{summary['severity_counts']['critical']}`")
    lines.append(f"- High: `{summary['severity_counts']['high']}`")
    lines.append(f"- Medium: `{summary['severity_counts']['medium']}`")
    lines.append(f"- Low: `{summary['severity_counts']['low']}`")
    lines.append(f"- Info: `{summary['severity_counts']['info']}`")
    lines.append("")
    lines.append("## Review Status")
    lines.append("")
    for status, count in summary["review_counts"].items():
        lines.append(f"- {status}: `{count}`")
    lines.append("")
    lines.append("## Module Summary")
    lines.append("")
    for module_summary in summary["module_summaries"]:
        counts = module_summary["severity_counts"]
        lines.append(
            f"- **{module_summary['module_name']}**: "
            f"{module_summary['finding_count']} findings "
            f"(critical {counts['critical']}, high {counts['high']}, medium {counts['medium']}, low {counts['low']}, info {counts['info']})"
        )
    lines.append("")
    lines.append("## Top Risks")
    lines.append("")
    for risk in top_risks:
        lines.append(
            f"- `{risk['severity']}` **{risk['module_name']}** - {risk['title']} "
            f"({risk['affected_asset']}, status: {risk['status']})"
        )
    lines.append("")
    lines.append("## Recommended Next Actions")
    lines.append("")
    for action in actions:
        lines.append(
            f"- `{action['severity']}` **{action['module_name']}** - {action['action']}"
        )
    lines.append("")
    lines.append("## Evidence Limitations")
    lines.append("")
    for limitation in _report_limitations():
        lines.append(f"- {limitation}")

    return "\n".join(lines)


def _build_html_report(modules: list[dict[str, Any]], summary: dict[str, Any], generated_at: str) -> str:
    module_cards = "\n".join(_html_module_card(module) for module in modules)
    risk_rows = "\n".join(_html_risk_row(risk) for risk in _top_risks(modules))
    action_items = "\n".join(_html_action_item(action) for action in _recommended_actions(modules))
    limitations = "".join(f"<li>{html.escape(item)}</li>" for item in _report_limitations())

    if not risk_rows:
        risk_rows = '<tr><td colspan="5">No findings loaded.</td></tr>'

    if not action_items:
        action_items = "<li>No recommended actions available from loaded findings.</li>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>CustosOps Executive Summary Pack</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  {_style()}
</head>
<body>
<main>
  <section class="hero">
    <p class="eyebrow">CustosOps Executive Summary Pack</p>
    <h1>Operational Evidence Summary</h1>
    <p class="muted">Generated: {html.escape(generated_at)}</p>
    <p class="muted">CustosOps combined currently loaded local evidence across modules. No remediation or external upload was performed.</p>
  </section>

  <section class="summary-grid">
    <div class="metric"><span>Modules</span><strong>{summary['module_count']}</strong></div>
    <div class="metric"><span>Total findings</span><strong>{summary['finding_count']}</strong></div>
    <div class="metric"><span>Critical</span><strong>{summary['severity_counts']['critical']}</strong></div>
    <div class="metric"><span>High</span><strong>{summary['severity_counts']['high']}</strong></div>
    <div class="metric"><span>Medium</span><strong>{summary['severity_counts']['medium']}</strong></div>
    <div class="metric"><span>Low</span><strong>{summary['severity_counts']['low']}</strong></div>
  </section>

  <section class="card">
    <p class="eyebrow">Review Status</p>
    <div class="review-grid">
      <div><span>Open</span><strong>{summary['review_counts']['open']}</strong></div>
      <div><span>Reviewed</span><strong>{summary['review_counts']['reviewed']}</strong></div>
      <div><span>Needs follow-up</span><strong>{summary['review_counts']['needs_follow_up']}</strong></div>
      <div><span>Accepted risk</span><strong>{summary['review_counts']['accepted_risk']}</strong></div>
      <div><span>False positive</span><strong>{summary['review_counts']['false_positive']}</strong></div>
    </div>
  </section>

  <section class="module-grid">
    {module_cards}
  </section>

  <section class="card">
    <p class="eyebrow">Top Risks</p>
    <table>
      <thead>
        <tr>
          <th>Severity</th>
          <th>Module</th>
          <th>Finding</th>
          <th>Asset</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {risk_rows}
      </tbody>
    </table>
  </section>

  <section class="card">
    <p class="eyebrow">Recommended Next Actions</p>
    <ul>{action_items}</ul>
  </section>

  <section class="card">
    <p class="eyebrow">Evidence Limitations</p>
    <ul>{limitations}</ul>
  </section>
</main>
</body>
</html>
"""


def _html_module_card(module: dict[str, Any]) -> str:
    summary = module["summary"]
    counts = summary["severity_counts"]
    evidence_size = summary["evidence_size"]

    return f"""<section class="card module-card">
    <p class="eyebrow">{html.escape(str(summary['module_name']))}</p>
    <h2>{summary['finding_count']} findings</h2>
    <p class="muted">Source: {html.escape(str(summary['source']))}</p>
    <p class="muted">Evidence: {html.escape(str(evidence_size))}</p>
    <dl>
      <div><dt>Critical</dt><dd>{counts['critical']}</dd></div>
      <div><dt>High</dt><dd>{counts['high']}</dd></div>
      <div><dt>Medium</dt><dd>{counts['medium']}</dd></div>
      <div><dt>Low</dt><dd>{counts['low']}</dd></div>
    </dl>
  </section>"""


def _html_risk_row(risk: dict[str, Any]) -> str:
    severity = html.escape(str(risk["severity"]))
    return f"""<tr>
      <td><span class="severity {severity}">{severity}</span></td>
      <td>{html.escape(str(risk['module_name']))}</td>
      <td>{html.escape(str(risk['title']))}<br><code>{html.escape(str(risk['finding_id']))}</code></td>
      <td>{html.escape(str(risk['affected_asset']))}</td>
      <td>{html.escape(str(risk['status']))}</td>
    </tr>"""


def _html_action_item(action: dict[str, Any]) -> str:
    return (
        f"<li><strong>{html.escape(str(action['module_name']))}</strong> "
        f"<span class=\"severity {html.escape(str(action['severity']))}\">{html.escape(str(action['severity']))}</span> "
        f"{html.escape(str(action['action']))}</li>"
    )


def _all_findings(modules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    for module in modules:
        findings.extend(module.get("findings", []))

    return findings


def _safe_severity(value: Any) -> str:
    lowered = str(value or "info").lower()

    if lowered in SEVERITY_ORDER:
        return lowered

    return "info"


def _evidence_size(module_id: str, evidence: dict[str, Any]) -> str:
    if module_id == "endpoint":
        endpoint_name = evidence.get("endpoint_name") or evidence.get("host_name") or "endpoint evidence"
        return str(endpoint_name)

    if module_id == "dns":
        records = evidence.get("records")

        if isinstance(records, list):
            return f"{len(records)} records"

        return "DNS evidence"

    if module_id == "app-log":
        parsed = evidence.get("parsed_entry_count")
        raw = evidence.get("raw_line_count")

        if parsed is not None:
            return f"{parsed} parsed log entries"

        if raw is not None:
            return f"{raw} raw log lines"

        return "application log evidence"

    if module_id == "windows-events":
        parsed = evidence.get("parsed_event_count")
        raw = evidence.get("raw_event_count")

        if parsed is not None:
            return f"{parsed} parsed events"

        if raw is not None:
            return f"{raw} raw events"

        return "Windows Event evidence"

    return "loaded evidence"


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):
        return value.model_dump()

    if hasattr(value, "dict"):
        return value.dict()

    return {}


def _report_limitations() -> list[str]:
    return [
        "This executive pack only summarizes evidence currently loaded in CustosOps.",
        "A sample or partial evidence export may not represent the full incident or environment.",
        "Findings should be validated against organizational policy, asset criticality, and change history.",
        "Review statuses and notes are local operator metadata.",
        "No remediation was performed by CustosOps.",
        "No evidence was uploaded externally by CustosOps.",
    ]


def _style() -> str:
    return """<style>
    :root { font-family: Inter, Segoe UI, Arial, sans-serif; color: #0f172a; background: #f8fafc; }
    body { margin: 0; background: #f8fafc; }
    main { width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: 32px 0 48px; }
    .hero, .card { background: white; border: 1px solid #e2e8f0; border-radius: 18px; box-shadow: 0 12px 34px rgba(15, 23, 42, 0.08); }
    .hero { padding: 30px; margin-bottom: 18px; }
    .eyebrow { color: #2563eb; text-transform: uppercase; letter-spacing: 0.12em; font-size: 0.75rem; font-weight: 800; margin: 0 0 8px; }
    h1 { margin: 0 0 10px; font-size: clamp(2.2rem, 5vw, 4rem); letter-spacing: -0.06em; }
    h2 { margin: 0 0 8px; }
    .muted { color: #475569; line-height: 1.6; }
    .summary-grid, .review-grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }
    .review-grid { grid-template-columns: repeat(5, minmax(0, 1fr)); }
    .metric, .review-grid div { background: #eff6ff; border: 1px solid #dbeafe; border-radius: 14px; padding: 14px; }
    .metric span, .review-grid span { display: block; color: #475569; font-size: 0.82rem; margin-bottom: 4px; }
    .metric strong, .review-grid strong { font-size: 1.3rem; }
    .module-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-bottom: 14px; }
    .card { padding: 20px; margin-bottom: 14px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; border-bottom: 1px solid #e2e8f0; padding: 12px 10px; vertical-align: top; }
    th { color: #475569; font-size: 0.82rem; }
    .severity { padding: 5px 9px; border-radius: 999px; text-transform: uppercase; font-size: 0.72rem; font-weight: 900; letter-spacing: 0.08em; white-space: nowrap; }
    .critical, .high { background: #fee2e2; color: #991b1b; }
    .medium { background: #fef3c7; color: #92400e; }
    .low { background: #dcfce7; color: #166534; }
    .info { background: #dbeafe; color: #1e40af; }
    dl { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 14px 0 0; }
    dt { color: #64748b; font-size: 0.78rem; }
    dd { margin: 4px 0 0; font-weight: 800; }
    li { margin-bottom: 8px; line-height: 1.45; }
    code { background: #f1f5f9; border-radius: 6px; padding: 2px 5px; }
    @media print { .card, .hero { box-shadow: none; } body { background: white; } }
    @media (max-width: 900px) { .summary-grid, .review-grid, .module-grid, dl { grid-template-columns: 1fr; } }
  </style>"""
