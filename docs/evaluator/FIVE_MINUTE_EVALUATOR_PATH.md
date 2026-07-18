# CustosOps Five-Minute Evaluator Path

This path is designed for a recruiter, hiring manager, or technical reviewer who wants to understand the project quickly without using production data.

## 0:00–0:45 — Confirm the boundary

Open **Overview** and verify that CustosOps is presented as a local-first, read-only defensive evidence console. It does not claim to be a SIEM, EDR, vulnerability scanner, tenant-monitoring service, or remediation platform.

## 0:45–1:45 — Review evidence findings

Open **Endpoint** and **DNS Hygiene**. Inspect:

- severity and confidence;
- affected asset and evidence values;
- why the finding matters;
- limitations;
- safe next steps and explicit non-actions.

All committed demonstrations use synthetic or local sample evidence.

## 1:45–2:45 — Follow an application-support investigation

Open **App Logs** and review the sample application-log workflow. The intended support pattern is:

1. collect or import evidence;
2. normalize it;
3. identify findings;
4. document limitations;
5. preserve an escalation-ready record.

## 2:45–3:45 — Generate and trace output

Open **Reports**, then **Archive** and **Run History**. Confirm that generated evidence can be represented as HTML, Markdown, or JSON and that report/run traceability is retained locally.

## 3:45–4:30 — Review public-safety controls

Open **Redaction**. Verify that report output can be previewed with field, pattern, and literal redaction controls before evidence is shared.

## 4:30–5:00 — Verify engineering evidence

Review the repository validation evidence:

- backend tests;
- frontend production build;
- Playwright ten-workspace and SOC workflow proof;
- Windows PowerShell/build verification;
- dependency security audit;
- supply-chain inventory;
- clean-machine Windows acceptance package.

## Recommended evaluator questions

- Where are confidence and limitations recorded?
- Which actions are intentionally excluded?
- How does evidence move from collection/import to report and archive?
- How are synthetic data and public-repository safety enforced?
- What would require escalation to engineering, security, or an administrator?
