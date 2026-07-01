import html
import json
from collections import Counter
from datetime import datetime, timezone

from app.analyzers.dns_hygiene import analyze_dns_evidence
from app.schemas.dns import DnsEvidence
from app.schemas.finding import SecurityFinding
from app.schemas.report import DnsReportResponse, ReportFormat


SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]


def build_dns_report(
    evidence: DnsEvidence,
    report_format: ReportFormat = "html",
    findings: list[SecurityFinding] | None = None,
) -> DnsReportResponse:
    final_findings = findings if findings is not None else analyze_dns_evidence(evidence)
    source = evidence.source_file or "dns-evidence"
    safe_source = _safe_filename(source)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")

    if report_format == "json":
        content = _build_json_report(evidence, final_findings)
        return DnsReportResponse(
            filename=f"custosops_dns_report_{safe_source}_{timestamp}.json",
            format="json",
            content_type="application/json",
            content=content,
        )

    if report_format == "markdown":
        content = _build_markdown_report(evidence, final_findings)
        return DnsReportResponse(
            filename=f"custosops_dns_report_{safe_source}_{timestamp}.md",
            format="markdown",
            content_type="text/markdown",
            content=content,
        )

    content = _build_html_report(evidence, final_findings)
    return DnsReportResponse(
        filename=f"custosops_dns_report_{safe_source}_{timestamp}.html",
        format="html",
        content_type="text/html",
        content=content,
    )


def _safe_filename(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)
    return cleaned.strip("_")[:80] or "dns-evidence"


def _summary_counts(findings: list[SecurityFinding]) -> dict[str, int]:
    counter = Counter(finding.severity for finding in findings)
    return {severity: int(counter.get(severity, 0)) for severity in SEVERITY_ORDER}


def _top_actions(findings: list[SecurityFinding]) -> list[str]:
    ordered = sorted(
        findings,
        key=lambda finding: SEVERITY_ORDER.index(finding.severity)
        if finding.severity in SEVERITY_ORDER
        else len(SEVERITY_ORDER),
    )

    actions: list[str] = []
    seen: set[str] = set()

    for finding in ordered:
        if not finding.safe_next_steps:
            continue

        action = f"{finding.title}: {finding.safe_next_steps[0]}"
        if action in seen:
            continue

        actions.append(action)
        seen.add(action)

        if len(actions) >= 7:
            break

    return actions


def _build_json_report(evidence: DnsEvidence, findings: list[SecurityFinding]) -> str:
    payload = {
        "report_type": "custosops.dns.v0.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": evidence.source_file,
        "summary": {
            "record_count": len(evidence.records),
            "finding_count": len(findings),
            "severity_counts": _summary_counts(findings),
            "top_actions": _top_actions(findings),
        },
        "evidence": evidence.model_dump(),
        "findings": [finding.model_dump() for finding in findings],
        "limitations": [
            "This report is based on imported DNS evidence.",
            "This is not a full DNS security assessment.",
            "DNS cleanup must be validated with service ownership and change control.",
            "No DNS records were modified by CustosOps.",
        ],
    }

    return json.dumps(payload, indent=2)


def _build_markdown_report(evidence: DnsEvidence, findings: list[SecurityFinding]) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    counts = _summary_counts(findings)
    top_actions = _top_actions(findings)

    lines: list[str] = []
    lines.append("# CustosOps DNS Hygiene Report")
    lines.append("")
    lines.append(f"Generated: {generated}")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- Source file: `{evidence.source_file or 'n/a'}`")
    lines.append(f"- DNS records analyzed: `{len(evidence.records)}`")
    lines.append(f"- Findings: `{len(findings)}`")
    for severity in SEVERITY_ORDER:
        lines.append(f"- {severity.title()}: `{counts[severity]}`")
    lines.append("")
    lines.append("## Top Recommended Actions")
    lines.append("")
    if top_actions:
        for action in top_actions:
            lines.append(f"- {action}")
    else:
        lines.append("- No major actions identified by current DNS rules.")
    lines.append("")
    lines.append("## Findings")
    lines.append("")

    for finding in findings:
        lines.append(f"### {finding.title}")
        lines.append("")
        lines.append(f"- Severity: `{finding.severity}`")
        lines.append(f"- Confidence: `{finding.confidence}`")
        lines.append(f"- Category: `{finding.category}`")
        lines.append(f"- Affected asset: `{finding.affected_asset}`")
        lines.append(f"- Finding ID: `{finding.finding_id}`")
        lines.append("")
        lines.append("Why it matters:")
        lines.append("")
        lines.append(finding.why_it_matters)
        lines.append("")
        lines.append("Evidence:")
        lines.append("")
        for item in finding.evidence:
            lines.append(f"- `{item.key}`: `{item.value}`")
        lines.append("")
        lines.append("Safe next steps:")
        lines.append("")
        for step in finding.safe_next_steps:
            lines.append(f"- {step}")
        lines.append("")
        lines.append("Limitations:")
        lines.append("")
        for limitation in finding.limitations:
            lines.append(f"- {limitation}")
        lines.append("")

    lines.append("## Report Limitations")
    lines.append("")
    lines.append("- This report is based on imported DNS evidence.")
    lines.append("- This is not a full DNS security assessment.")
    lines.append("- DNS cleanup must be validated with service ownership and change control.")
    lines.append("- No DNS records were modified by CustosOps.")
    lines.append("")

    return "\n".join(lines)


def _build_html_report(evidence: DnsEvidence, findings: list[SecurityFinding]) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    counts = _summary_counts(findings)
    top_actions = _top_actions(findings)

    finding_cards = "\n".join(_finding_to_html(finding) for finding in findings)
    actions_html = "".join(f"<li>{html.escape(action)}</li>" for action in top_actions)
    if not actions_html:
        actions_html = "<li>No major actions identified by current DNS rules.</li>"

    source_file = evidence.source_file or "n/a"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>CustosOps DNS Hygiene Report</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {{
      font-family: Inter, Segoe UI, Arial, sans-serif;
      color: #0f172a;
      background: #f8fafc;
    }}
    body {{
      margin: 0;
      background: #f8fafc;
    }}
    main {{
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 32px 0 48px;
    }}
    .hero, .card {{
      background: white;
      border: 1px solid #e2e8f0;
      border-radius: 18px;
      box-shadow: 0 12px 34px rgba(15, 23, 42, 0.08);
    }}
    .hero {{
      padding: 28px;
      margin-bottom: 18px;
    }}
    .eyebrow {{
      color: #2563eb;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 0.75rem;
      font-weight: 800;
      margin: 0 0 8px;
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: clamp(2rem, 5vw, 3.6rem);
      letter-spacing: -0.06em;
    }}
    .muted {{
      color: #475569;
      line-height: 1.6;
    }}
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 12px;
      margin: 18px 0;
    }}
    .metric {{
      background: #eff6ff;
      border: 1px solid #dbeafe;
      border-radius: 14px;
      padding: 14px;
    }}
    .metric span {{
      display: block;
      color: #475569;
      font-size: 0.82rem;
      margin-bottom: 4px;
    }}
    .metric strong {{
      font-size: 1.25rem;
    }}
    .card {{
      padding: 20px;
      margin-bottom: 14px;
    }}
    .finding-top {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: start;
      margin-bottom: 10px;
    }}
    .severity {{
      padding: 5px 9px;
      border-radius: 999px;
      text-transform: uppercase;
      font-size: 0.72rem;
      font-weight: 900;
      letter-spacing: 0.08em;
    }}
    .critical, .high {{
      background: #fee2e2;
      color: #991b1b;
    }}
    .medium {{
      background: #fef3c7;
      color: #92400e;
    }}
    .low {{
      background: #dcfce7;
      color: #166534;
    }}
    .info {{
      background: #dbeafe;
      color: #1e40af;
    }}
    dl {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin: 14px 0;
    }}
    dt {{
      color: #64748b;
      font-size: 0.78rem;
    }}
    dd {{
      margin: 4px 0 0;
      font-weight: 800;
      word-break: break-word;
    }}
    li {{
      margin-bottom: 6px;
      line-height: 1.45;
    }}
    code {{
      background: #f1f5f9;
      border-radius: 6px;
      padding: 2px 5px;
    }}
    .columns {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
    }}
    @media print {{
      .card, .hero {{
        box-shadow: none;
      }}
      body {{
        background: white;
      }}
    }}
    @media (max-width: 900px) {{
      .summary-grid, .columns, dl {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
<main>
  <section class="hero">
    <p class="eyebrow">CustosOps DNS Hygiene Report</p>
    <h1>DNS Hygiene Review</h1>
    <p class="muted">Generated: {html.escape(generated)}</p>
    <p class="muted">Source file: {html.escape(source_file)}</p>
    <p class="muted">This report is based on imported DNS evidence. CustosOps did not modify DNS records.</p>
  </section>

  <section class="summary-grid">
    <div class="metric"><span>Records</span><strong>{len(evidence.records)}</strong></div>
    <div class="metric"><span>Findings</span><strong>{len(findings)}</strong></div>
    <div class="metric"><span>Critical</span><strong>{counts["critical"]}</strong></div>
    <div class="metric"><span>High</span><strong>{counts["high"]}</strong></div>
    <div class="metric"><span>Medium</span><strong>{counts["medium"]}</strong></div>
    <div class="metric"><span>Low</span><strong>{counts["low"]}</strong></div>
  </section>

  <section class="card">
    <p class="eyebrow">Top Recommended Actions</p>
    <ul>
      {actions_html}
    </ul>
  </section>

  {finding_cards}

  <section class="card">
    <p class="eyebrow">Report Limitations</p>
    <ul>
      <li>This report is based on imported DNS evidence.</li>
      <li>This is not a full DNS security assessment.</li>
      <li>DNS cleanup must be validated with service ownership and change control.</li>
      <li>No DNS records were modified by CustosOps.</li>
    </ul>
  </section>
</main>
</body>
</html>"""


def _finding_to_html(finding: SecurityFinding) -> str:
    next_steps = "".join(f"<li>{html.escape(step)}</li>" for step in finding.safe_next_steps)
    limitations = "".join(f"<li>{html.escape(item)}</li>" for item in finding.limitations)
    evidence_html = "".join(
        f"<li><code>{html.escape(item.key)}</code>: {html.escape(item.value)}</li>"
        for item in finding.evidence
    )

    return f"""<section class="card">
  <div class="finding-top">
    <div>
      <p class="eyebrow">{html.escape(finding.category)}</p>
      <h2>{html.escape(finding.title)}</h2>
    </div>
    <span class="severity {html.escape(finding.severity)}">{html.escape(finding.severity)}</span>
  </div>

  <p class="muted">{html.escape(finding.why_it_matters)}</p>

  <dl>
    <div><dt>Finding ID</dt><dd>{html.escape(finding.finding_id)}</dd></div>
    <div><dt>Confidence</dt><dd>{html.escape(finding.confidence)}</dd></div>
    <div><dt>Affected asset</dt><dd>{html.escape(finding.affected_asset)}</dd></div>
    <div><dt>Status</dt><dd>{html.escape(finding.status)}</dd></div>
  </dl>

  <h3>Evidence</h3>
  <ul>{evidence_html}</ul>

  <div class="columns">
    <div>
      <h3>Safe next steps</h3>
      <ul>{next_steps}</ul>
    </div>
    <div>
      <h3>Limitations</h3>
      <ul>{limitations}</ul>
    </div>
  </div>
</section>"""