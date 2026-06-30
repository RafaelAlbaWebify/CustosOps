import { ChangeEvent, useEffect, useMemo, useState } from "react";

type Health = {
  status: string;
  product: string;
  product_full_name: string;
  version: string;
};

type ModuleInfo = {
  id: string;
  name: string;
  group: string;
  status: string;
  description: string;
};

type EvidenceItem = {
  source: string;
  key: string;
  value: string;
};

type Finding = {
  finding_id: string;
  title: string;
  severity: string;
  confidence: string;
  category: string;
  affected_asset: string;
  evidence: EvidenceItem[];
  why_it_matters: string;
  limitations: string[];
  safe_next_steps: string[];
  non_actions: string[];
  status?: string;
};

type ReportFormat = "html" | "markdown" | "json";

type ReportResponse = {
  filename: string;
  format: ReportFormat;
  content_type: string;
  content: string;
};

const API_BASE = "http://127.0.0.1:8000";
const SEVERITY_ORDER = ["info", "low", "medium", "high", "critical"];

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [modules, setModules] = useState<ModuleInfo[]>([]);
  const [foundationFindings, setFoundationFindings] = useState<Finding[]>([]);
  const [endpointFindings, setEndpointFindings] = useState<Finding[]>([]);
  const [importedEndpointFindings, setImportedEndpointFindings] = useState<Finding[]>([]);
  const [importedEndpointEvidence, setImportedEndpointEvidence] = useState<unknown | null>(null);
  const [importFileName, setImportFileName] = useState<string>("");
  const [importError, setImportError] = useState<string>("");
  const [reportError, setReportError] = useState<string>("");
  const [error, setError] = useState<string>("");

  const highestImportedSeverity = useMemo(() => {
    if (importedEndpointFindings.length === 0) {
      return "none";
    }

    return [...importedEndpointFindings]
      .sort(
        (a, b) =>
          SEVERITY_ORDER.indexOf(b.severity) - SEVERITY_ORDER.indexOf(a.severity)
      )[0].severity;
  }, [importedEndpointFindings]);

  const severityCounts = useMemo(() => {
    const counts: Record<string, number> = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      info: 0
    };

    for (const finding of importedEndpointFindings) {
      counts[finding.severity] = (counts[finding.severity] ?? 0) + 1;
    }

    return counts;
  }, [importedEndpointFindings]);

  const importedAsset = useMemo(() => {
    if (importedEndpointFindings.length === 0) {
      return "n/a";
    }

    return importedEndpointFindings[0].affected_asset;
  }, [importedEndpointFindings]);

  const activeModuleCount = useMemo(() => {
    return modules.filter((module) => module.status !== "planned").length;
  }, [modules]);

  useEffect(() => {
    async function loadFoundationData() {
      try {
        const healthResponse = await fetch(`${API_BASE}/api/health`);
        const modulesResponse = await fetch(`${API_BASE}/api/modules`);
        const foundationFindingsResponse = await fetch(`${API_BASE}/api/sample-findings`);
        const endpointFindingsResponse = await fetch(`${API_BASE}/api/endpoint/sample-findings`);

        if (
          !healthResponse.ok ||
          !modulesResponse.ok ||
          !foundationFindingsResponse.ok ||
          !endpointFindingsResponse.ok
        ) {
          throw new Error("One or more backend endpoints failed.");
        }

        setHealth(await healthResponse.json());
        setModules((await modulesResponse.json()).modules);
        setFoundationFindings((await foundationFindingsResponse.json()).findings);
        setEndpointFindings((await endpointFindingsResponse.json()).findings);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown frontend error");
      }
    }

    loadFoundationData();
  }, []);

  async function handleEndpointEvidenceImport(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    setImportError("");
    setReportError("");
    setImportedEndpointFindings([]);
    setImportedEndpointEvidence(null);
    setImportFileName("");

    if (!file) {
      return;
    }

    try {
      const text = await file.text();
      const payload = JSON.parse(text);

      const response = await fetch(`${API_BASE}/api/endpoint/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const responseText = await response.text();
        throw new Error(`Backend rejected the evidence file: ${response.status} ${responseText}`);
      }

      const data = await response.json();

      setImportFileName(file.name);
      setImportedEndpointEvidence(payload);
      setImportedEndpointFindings(data.findings);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Unable to import endpoint evidence.");
    } finally {
      event.target.value = "";
    }
  }

  async function handleReportDownload(format: ReportFormat) {
    setReportError("");

    if (!importedEndpointEvidence || importedEndpointFindings.length === 0) {
      setReportError("Import endpoint evidence before generating a report.");
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/reports/endpoint`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          evidence: importedEndpointEvidence,
          findings: importedEndpointFindings,
          format
        })
      });

      if (!response.ok) {
        const responseText = await response.text();
        throw new Error(`Report generation failed: ${response.status} ${responseText}`);
      }

      const data: ReportResponse = await response.json();
      downloadTextFile(data.filename, data.content, data.content_type);
    } catch (err) {
      setReportError(err instanceof Error ? err.message : "Unable to generate report.");
    }
  }

  return (
    <main className="app-shell">
      <section className="hero hero-compact">
        <div>
          <p className="eyebrow">Cybersecurity Evidence and Posture Platform</p>
          <h1>CustosOps</h1>
          <p className="summary">
            Local-first cybersecurity evidence collection, posture review, risk
            prioritization, and remediation-ready reporting for Microsoft and
            Windows environments.
          </p>
        </div>

        <div className="status-card">
          <span className={health?.status === "ok" ? "status-ok" : "status-warn"} />
          <div>
            <strong>{health ? "Backend online" : "Backend not confirmed"}</strong>
            <p>{health ? health.version : "Start FastAPI on port 8000."}</p>
          </div>
        </div>
      </section>

      {error && <section className="alert">{error}</section>}

      <section className="kpi-grid">
        <MetricCard label="Imported findings" value={String(importedEndpointFindings.length)} />
        <MetricCard label="Highest severity" value={highestImportedSeverity.toUpperCase()} />
        <MetricCard label="Affected asset" value={importedAsset} />
        <MetricCard label="Active modules" value={`${activeModuleCount}/${modules.length}`} />
      </section>

      <section className="top-grid">
        <article className="panel panel-compact">
          <div className="section-heading compact-heading">
            <div>
              <p className="eyebrow">Platform</p>
              <h2>Modules</h2>
            </div>
          </div>

          <div className="module-compact-grid">
            {modules.map((module) => (
              <div className="module-pill-card" key={module.id}>
                <div>
                  <strong>{module.name}</strong>
                  <p>{module.description}</p>
                </div>
                <span>{module.status}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="panel panel-compact">
          <div className="section-heading compact-heading">
            <div>
              <p className="eyebrow">Foundation</p>
              <h2>Status</h2>
            </div>
          </div>

          {foundationFindings.map((finding) => (
            <div className="foundation-callout" key={finding.finding_id}>
              <div className="foundation-topline">
                <strong>{finding.title}</strong>
                <span className={`severity severity-${finding.severity}`}>{finding.severity}</span>
              </div>
              <p>{finding.why_it_matters}</p>
            </div>
          ))}
        </article>
      </section>

      <section className="panel panel-compact">
        <div className="section-heading compact-heading">
          <div>
            <p className="eyebrow">Local Evidence Import v0.1</p>
            <h2>Analyze endpoint evidence JSON</h2>
            <p className="section-summary">
              Select the JSON generated by the local read-only collector.
            </p>
          </div>
          <span className="count-pill">local only</span>
        </div>

        <div className="import-toolbar">
          <label className="file-import">
            <input
              type="file"
              accept=".json,application/json"
              onChange={handleEndpointEvidenceImport}
            />
            <span>Select endpoint evidence JSON</span>
          </label>

          <div className="import-help">
            <strong>Expected:</strong>
            <code>reports\endpoint-evidence.local.json</code>
          </div>

          {importFileName && (
            <div className="import-help">
              <strong>Loaded:</strong>
              <code>{importFileName}</code>
            </div>
          )}
        </div>

        {importError && <div className="alert inline-alert">{importError}</div>}

        <div className="summary-strip">
          <SummaryChip label="Critical" value={severityCounts.critical} tone="critical" />
          <SummaryChip label="High" value={severityCounts.high} tone="high" />
          <SummaryChip label="Medium" value={severityCounts.medium} tone="medium" />
          <SummaryChip label="Low" value={severityCounts.low} tone="low" />
          <SummaryChip label="Info" value={severityCounts.info} tone="info" />
        </div>

        <div className="report-actions">
          <button
            type="button"
            disabled={importedEndpointFindings.length === 0}
            onClick={() => handleReportDownload("html")}
          >
            Download HTML report
          </button>
          <button
            type="button"
            disabled={importedEndpointFindings.length === 0}
            onClick={() => handleReportDownload("markdown")}
          >
            Download Markdown
          </button>
          <button
            type="button"
            disabled={importedEndpointFindings.length === 0}
            onClick={() => handleReportDownload("json")}
          >
            Download JSON
          </button>
        </div>

        {reportError && <div className="alert inline-alert">{reportError}</div>}
      </section>

      <section className="panel panel-compact">
        <div className="section-heading compact-heading">
          <div>
            <p className="eyebrow">Imported Findings</p>
            <h2>Compact review</h2>
            <p className="section-summary">
              Everything important is visible here first. Expand rows only when you need detail.
            </p>
          </div>
          <span className="count-pill">{importedEndpointFindings.length} findings</span>
        </div>

        {importedEndpointFindings.length === 0 ? (
          <div className="empty-state">
            Import a local endpoint evidence JSON file to see real findings here.
          </div>
        ) : (
          <div className="finding-list">
            {importedEndpointFindings.map((finding) => (
              <FindingAccordion finding={finding} key={finding.finding_id} />
            ))}
          </div>
        )}
      </section>

      <section className="panel panel-compact">
        <details className="sample-section">
          <summary>
            <div>
              <p className="eyebrow">Sample data</p>
              <strong>Sample endpoint findings</strong>
            </div>
            <span className="count-pill">{endpointFindings.length} findings</span>
          </summary>

          <div className="finding-list details-body">
            {endpointFindings.map((finding) => (
              <FindingAccordion finding={finding} key={finding.finding_id} />
            ))}
          </div>
        </details>
      </section>
    </main>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="metric-card">
      <p>{label}</p>
      <strong>{value}</strong>
    </article>
  );
}

function SummaryChip({
  label,
  value,
  tone
}: {
  label: string;
  value: number;
  tone: string;
}) {
  return (
    <div className={`summary-chip tone-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function FindingAccordion({ finding }: { finding: Finding }) {
  return (
    <details className="finding-row">
      <summary>
        <div className="finding-summary-main">
          <span className={`severity severity-${finding.severity}`}>{finding.severity}</span>
          <strong>{finding.title}</strong>
        </div>

        <div className="finding-summary-meta">
          <span>{finding.category}</span>
          <span>{finding.affected_asset}</span>
          <span>{finding.confidence} confidence</span>
        </div>
      </summary>

      <div className="finding-body">
        <p className="finding-body-text">{finding.why_it_matters}</p>

        <div className="finding-columns">
          <div>
            <h4>Safe next steps</h4>
            <ul>
              {finding.safe_next_steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ul>
          </div>

          <div>
            <h4>Limitations</h4>
            <ul>
              {finding.limitations.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>

        {finding.evidence.length > 0 && (
          <div className="evidence-inline">
            {finding.evidence.map((item) => (
              <code key={`${item.source}-${item.key}`}>
                {item.key}: {item.value}
              </code>
            ))}
          </div>
        )}
      </div>
    </details>
  );
}

function downloadTextFile(filename: string, content: string, contentType: string) {
  const blob = new Blob([content], { type: contentType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");

  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();

  URL.revokeObjectURL(url);
}