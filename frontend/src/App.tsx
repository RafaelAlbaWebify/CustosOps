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
  archived?: boolean;
  archived_path?: string | null;
  archive_entry_id?: string | null;
};

type ArchiveEntry = {
  id: string;
  report_type: string;
  format: string;
  filename: string;
  relative_path: string;
  content_type: string;
  generated_at_utc: string;
  size_bytes: number;
};

type SeverityCounts = Record<string, number>;

const API_BASE = "http://127.0.0.1:8000";
const SEVERITY_ORDER = ["info", "low", "medium", "high", "critical"];

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [modules, setModules] = useState<ModuleInfo[]>([]);
  const [foundationFindings, setFoundationFindings] = useState<Finding[]>([]);

  const [endpointSampleFindings, setEndpointSampleFindings] = useState<Finding[]>([]);
  const [importedEndpointFindings, setImportedEndpointFindings] = useState<Finding[]>([]);
  const [importedEndpointEvidence, setImportedEndpointEvidence] = useState<unknown | null>(null);
  const [endpointFileName, setEndpointFileName] = useState<string>("");
  const [endpointCollecting, setEndpointCollecting] = useState<boolean>(false);

  const [dnsSampleFindings, setDnsSampleFindings] = useState<Finding[]>([]);
  const [importedDnsFindings, setImportedDnsFindings] = useState<Finding[]>([]);
  const [importedDnsEvidence, setImportedDnsEvidence] = useState<unknown | null>(null);
  const [dnsFileName, setDnsFileName] = useState<string>("");
  const [dnsImportMode, setDnsImportMode] = useState<string>("sample");
  const [dnsParsedRecordCount, setDnsParsedRecordCount] = useState<number | null>(null);
  const [dnsIgnoredRowCount, setDnsIgnoredRowCount] = useState<number | null>(null);
  const [dnsWarnings, setDnsWarnings] = useState<string[]>([]);

  const [appLogFindings, setAppLogFindings] = useState<Finding[]>([]);
  const [appLogEvidence, setAppLogEvidence] = useState<unknown | null>(null);
  const [appLogFileName, setAppLogFileName] = useState<string>("");
  const [appLogWarnings, setAppLogWarnings] = useState<string[]>([]);

  const [reportArchive, setReportArchive] = useState<ArchiveEntry[]>([]);

  const [importError, setImportError] = useState<string>("");
  const [reportError, setReportError] = useState<string>("");
  const [error, setError] = useState<string>("");

  const endpointFindingsToShow = importedEndpointFindings.length > 0 ? importedEndpointFindings : endpointSampleFindings;
  const dnsFindingsToShow = importedDnsFindings.length > 0 ? importedDnsFindings : dnsSampleFindings;

  const endpointSeverityCounts = useMemo(() => getSeverityCounts(endpointFindingsToShow), [endpointFindingsToShow]);
  const dnsSeverityCounts = useMemo(() => getSeverityCounts(dnsFindingsToShow), [dnsFindingsToShow]);
  const appLogSeverityCounts = useMemo(() => getSeverityCounts(appLogFindings), [appLogFindings]);

  const endpointHighestSeverity = getHighestSeverity(endpointFindingsToShow);
  const dnsHighestSeverity = getHighestSeverity(dnsFindingsToShow);
  const endpointAsset = getAffectedAsset(endpointFindingsToShow);

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
        const dnsFindingsResponse = await fetch(`${API_BASE}/api/dns/sample-findings`);

        if (
          !healthResponse.ok ||
          !modulesResponse.ok ||
          !foundationFindingsResponse.ok ||
          !endpointFindingsResponse.ok ||
          !dnsFindingsResponse.ok
        ) {
          throw new Error("One or more backend endpoints failed.");
        }

        setHealth(await healthResponse.json());
        setModules((await modulesResponse.json()).modules);
        setFoundationFindings((await foundationFindingsResponse.json()).findings);
        setEndpointSampleFindings((await endpointFindingsResponse.json()).findings);
        setDnsSampleFindings((await dnsFindingsResponse.json()).findings);
        await loadReportArchive();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown frontend error");
      }
    }

    loadFoundationData();
  }, []);

  async function loadReportArchive() {
    const response = await fetch(`${API_BASE}/api/reports/archive`);

    if (!response.ok) {
      return;
    }

    const data = await response.json();
    setReportArchive(data.reports ?? []);
  }

  async function handleEndpointLocalCollect() {
    setImportError("");
    setReportError("");
    setEndpointCollecting(true);

    try {
      const response = await fetch(`${API_BASE}/api/endpoint/collect-local`, {
        method: "POST"
      });

      if (!response.ok) {
        const responseText = await response.text();
        throw new Error(`Local endpoint collection failed: ${response.status} ${responseText}`);
      }

      const data = await response.json();

      setEndpointFileName(data.output_path || "reports/endpoint-evidence.local.json");
      setImportedEndpointEvidence(data.evidence);
      setImportedEndpointFindings(data.findings);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Unable to collect local endpoint evidence.");
    } finally {
      setEndpointCollecting(false);
    }
  }
  async function handleEndpointEvidenceImport(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    setImportError("");
    setReportError("");
    setImportedEndpointFindings([]);
    setImportedEndpointEvidence(null);
    setEndpointFileName("");

    if (!file) {
      return;
    }

    try {
      const text = await file.text();
      const payload = JSON.parse(text);
      const evidencePayload = normalizeEndpointEvidencePayload(payload);

      const response = await fetch(`${API_BASE}/api/endpoint/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(evidencePayload)
      });

      if (!response.ok) {
        const responseText = await response.text();
        throw new Error(`Backend rejected the endpoint evidence file: ${response.status} ${responseText}`);
      }

      const data = await response.json();

      setEndpointFileName(file.name);
      setImportedEndpointEvidence(evidencePayload);
      setImportedEndpointFindings(data.findings);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Unable to import endpoint evidence.");
    } finally {
      event.target.value = "";
    }
  }

  function handleDnsTemplateDownload() {
    window.open(`${API_BASE}/api/dns/csv-template`, "_blank", "noopener,noreferrer");
  }
  async function handleDnsEvidenceImport(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    resetDnsImportState();

    if (!file) {
      return;
    }

    try {
      const text = await file.text();
      const payload = JSON.parse(text);

      const response = await fetch(`${API_BASE}/api/dns/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const responseText = await response.text();
        throw new Error(`Backend rejected the DNS evidence file: ${response.status} ${responseText}`);
      }

      const data = await response.json();

      setDnsFileName(file.name);
      setDnsImportMode("json");
      setImportedDnsEvidence(payload);
      setImportedDnsFindings(data.findings);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Unable to import DNS evidence.");
    } finally {
      event.target.value = "";
    }
  }

  async function handleDnsCsvImport(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    resetDnsImportState();

    if (!file) {
      return;
    }

    try {
      const text = await file.text();

      const response = await fetch(`${API_BASE}/api/dns/import-csv`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          filename: file.name,
          content: text
        })
      });

      if (!response.ok) {
        const responseText = await response.text();
        throw new Error(`Backend rejected the DNS CSV file: ${response.status} ${responseText}`);
      }

      const data = await response.json();

      setDnsFileName(file.name);
      setDnsImportMode("csv");
      setDnsParsedRecordCount(data.parsed_record_count);
      setDnsIgnoredRowCount(data.ignored_row_count);
      setDnsWarnings(data.warnings ?? []);
      setImportedDnsEvidence(data.evidence);
      setImportedDnsFindings(data.findings);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Unable to import DNS CSV.");
    } finally {
      event.target.value = "";
    }
  }

  async function handleAppLogImport(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    setImportError("");
    setReportError("");
    setAppLogFindings([]);
    setAppLogEvidence(null);
    setAppLogFileName("");
    setAppLogWarnings([]);

    if (!file) {
      return;
    }

    try {
      const text = await file.text();

      const response = await fetch(`${API_BASE}/api/app-log/import`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          filename: file.name,
          content: text
        })
      });

      if (!response.ok) {
        const responseText = await response.text();
        throw new Error(`Backend rejected the app log file: ${response.status} ${responseText}`);
      }

      const data = await response.json();

      setAppLogFileName(file.name);
      setAppLogEvidence(data.evidence);
      setAppLogFindings(data.findings);
      setAppLogWarnings(data.warnings ?? []);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Unable to import application log.");
    } finally {
      event.target.value = "";
    }
  }

  async function handleAppLogReportDownload(format: ReportFormat) {
    setReportError("");

    if (!appLogEvidence || appLogFindings.length === 0) {
      setReportError("Import an application log before generating an app log report.");
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/reports/app-log`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          evidence: appLogEvidence,
          findings: appLogFindings,
          format,
          archive: true
        })
      });

      if (!response.ok) {
        const responseText = await response.text();
        throw new Error(`Application log report generation failed: ${response.status} ${responseText}`);
      }

      const data: ReportResponse = await response.json();
      downloadTextFile(data.filename, data.content, data.content_type);
      await loadReportArchive();
    } catch (err) {
      setReportError(err instanceof Error ? err.message : "Unable to generate application log report.");
    }
  }
  function resetDnsImportState() {
    setImportError("");
    setImportedDnsFindings([]);
    setImportedDnsEvidence(null);
    setDnsFileName("");
    setDnsImportMode("sample");
    setDnsParsedRecordCount(null);
    setDnsIgnoredRowCount(null);
    setDnsWarnings([]);
  }

  async function handleEndpointReportDownload(format: ReportFormat) {
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
          format,
          archive: true
        })
      });

      if (!response.ok) {
        const responseText = await response.text();
        throw new Error(`Report generation failed: ${response.status} ${responseText}`);
      }

      const data: ReportResponse = await response.json();
      downloadTextFile(data.filename, data.content, data.content_type);
      await loadReportArchive();
    } catch (err) {
      setReportError(err instanceof Error ? err.message : "Unable to generate endpoint report.");
    }
  }

  async function handleDnsReportDownload(format: ReportFormat) {
    setReportError("");

    if (!importedDnsEvidence || importedDnsFindings.length === 0) {
      setReportError("Import DNS evidence JSON or DNS Audit CSV before generating a DNS report.");
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/reports/dns`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          evidence: importedDnsEvidence,
          findings: importedDnsFindings,
          format,
          archive: true
        })
      });

      if (!response.ok) {
        const responseText = await response.text();
        throw new Error(`DNS report generation failed: ${response.status} ${responseText}`);
      }

      const data: ReportResponse = await response.json();
      downloadTextFile(data.filename, data.content, data.content_type);
      await loadReportArchive();
    } catch (err) {
      setReportError(err instanceof Error ? err.message : "Unable to generate DNS report.");
    }
  }

  async function handleArchiveDelete(entryId: string) {
    const confirmed = window.confirm("Delete this archived report from the local CustosOps archive?");

    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/reports/archive/${entryId}`, {
        method: "DELETE"
      });

      if (!response.ok) {
        const responseText = await response.text();
        throw new Error(`Delete failed: ${response.status} ${responseText}`);
      }

      await loadReportArchive();
    } catch (err) {
      setReportError(err instanceof Error ? err.message : "Unable to delete archived report.");
    }
  }

  function handleArchiveOpen(entryId: string) {
    window.open(`${API_BASE}/api/reports/archive/${entryId}/open`, "_blank", "noopener,noreferrer");
  }

  function handleArchiveDownload(entryId: string) {
    window.open(`${API_BASE}/api/reports/archive/${entryId}/download`, "_blank", "noopener,noreferrer");
  }
  const dnsModeLabel = getDnsModeLabel(dnsImportMode);

  return (
    <div className="product-frame">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">C</div>
          <span>CustosOps</span>
        </div>

        <nav className="side-nav">
          <a className="active" href="#overview"><span>OV</span>Overview</a>
          <a href="#endpoint"><span>EP</span>Endpoint</a>
          <a href="#dns"><span>DN</span>DNS Hygiene</a>
          <a href="#app-log"><span>LG</span>App Logs</a>
          <a href="#reports"><span>RP</span>Reports</a>
          <a href="#archive"><span>AR</span>Archive</a>
        </nav>

        <div className="sidebar-card">
          <div className="mini-shield">CO</div>
          <strong>CustosOps v1.0</strong>
          <p>Cybersecurity Evidence and Posture Platform</p>
        </div>

        <div className="sidebar-help">
          <span>?</span>
          Help & Docs
        </div>
      </aside>

      <div className="main-area">
        <header className="topbar">
          <div>
            <p className="page-label">Overview</p>
          </div>

          <div className="topbar-actions">
            <div className="backend-status">
              <span className={health?.status === "ok" ? "dot ok" : "dot warn"} />
              {health?.status === "ok" ? "Backend Online" : "Backend Not Confirmed"}
            </div>
            <div className="avatar">AD</div>
          </div>
        </header>

        <main className="dashboard">
          {error && <section className="alert banner-alert">{error}</section>}

          <section className="kpi-row">
            <KpiCard icon="EP" label="Endpoint Findings" value={String(endpointFindingsToShow.length)} note={endpointAsset === "n/a" ? "Awaiting import" : `Asset ${endpointAsset}`} />
            <KpiCard icon="DN" label="DNS Max Severity" value={capitalize(dnsHighestSeverity)} note={`${dnsFindingsToShow.length} DNS findings`} highlight />
            <KpiCard icon="LG" label="App Log Findings" value={String(appLogFindings.length)} note={appLogFileName || "Awaiting log import"} />
            <KpiCard icon="AR" label="Archived Reports" value={String(reportArchive.length)} note="In local archive" />
          </section>

          <section className="dashboard-grid">
            <section className="card evidence-card" id="endpoint">
              <div className="card-header">
                <div>
                  <p className="eyebrow">Endpoint</p>
                  <h2>Endpoint Security Evidence</h2>
                </div>
                <div className="button-group">
                  <button
                    className="button"
                    type="button"
                    disabled={endpointCollecting}
                    onClick={handleEndpointLocalCollect}
                  >
                    {endpointCollecting ? "Collecting..." : "Collect Local"}
                  </button>
                  <label className="button import-button">
                    <input type="file" accept=".json,application/json" onChange={handleEndpointEvidenceImport} />
                    Import JSON
                  </label>
                </div>
              </div>

              <SeverityStrip counts={endpointSeverityCounts} />

              <div className="action-row">
                <button disabled={importedEndpointFindings.length === 0} onClick={() => handleEndpointReportDownload("html")}>Download HTML</button>
                <button disabled={importedEndpointFindings.length === 0} onClick={() => handleEndpointReportDownload("markdown")}>Download Markdown</button>
                <button disabled={importedEndpointFindings.length === 0} onClick={() => handleEndpointReportDownload("json")}>Download JSON</button>
              </div>

              {endpointFileName && <p className="loaded-file">Loaded: {endpointFileName}</p>}

              <div className="table-panel">
                <div className="table-title">
                  <strong>Findings Summary</strong>
                  <span>{endpointFindingsToShow.length} findings</span>
                </div>

                <div className="finding-table endpoint-table">
                  <div className="table-head">
                    <span>Severity</span>
                    <span>Control / Finding</span>
                    <span>Status</span>
                    <span>Endpoint</span>
                  </div>

                  {endpointFindingsToShow.slice(0, 6).map((finding) => (
                    <div className="table-row" key={finding.finding_id}>
                      <SeverityDot severity={finding.severity} />
                      <span>{getEndpointControl(finding)}</span>
                      <span>{getEndpointStatus(finding)}</span>
                      <span>{finding.affected_asset}</span>
                    </div>
                  ))}
                </div>
              </div>

              <a className="card-link" href="#endpoint">View all endpoint findings</a>
            </section>

            <section className="card evidence-card" id="dns">
              <div className="card-header">
                <div>
                  <p className="eyebrow">DNS Hygiene</p>
                  <h2>DNS Hygiene</h2>
                </div>
                <div className="button-group">
                  <button className="button subtle" type="button" onClick={handleDnsTemplateDownload}>
                    CSV Template
                  </button>
                  <label className="button import-button">
                    <input type="file" accept=".json,application/json" onChange={handleDnsEvidenceImport} />
                    Import JSON
                  </label>
                  <label className="button import-button green">
                    <input type="file" accept=".csv,text/csv" onChange={handleDnsCsvImport} />
                    Import CSV
                  </label>
                </div>
              </div>

              <SeverityStrip counts={dnsSeverityCounts} />

              <div className="action-row">
                <button disabled={!importedDnsEvidence || importedDnsFindings.length === 0} onClick={() => handleDnsReportDownload("html")}>Download HTML</button>
                <button disabled={!importedDnsEvidence || importedDnsFindings.length === 0} onClick={() => handleDnsReportDownload("markdown")}>Download Markdown</button>
                <button disabled={!importedDnsEvidence || importedDnsFindings.length === 0} onClick={() => handleDnsReportDownload("json")}>Download JSON</button>
              </div>

              <div className="dns-meta-row">
                <span>{dnsModeLabel}</span>
                {dnsParsedRecordCount !== null && <span>{dnsParsedRecordCount} parsed</span>}
                {dnsIgnoredRowCount !== null && <span>{dnsIgnoredRowCount} ignored</span>}
              </div>

              {dnsFileName && <p className="loaded-file">Loaded: {dnsFileName}</p>}
              {dnsWarnings.length > 0 && <p className="warning-text">{dnsWarnings.join(" | ")}</p>}

              <div className="table-panel">
                <div className="table-title">
                  <strong>Parsed Records</strong>
                  <span>{dnsFindingsToShow.length} findings</span>
                </div>

                <div className="finding-table dns-table">
                  <div className="table-head">
                    <span>Severity</span>
                    <span>Issue</span>
                    <span>Record</span>
                    <span>Value</span>
                    <span>Type</span>
                  </div>

                  {dnsFindingsToShow.slice(0, 6).map((finding) => (
                    <div className="table-row" key={`${finding.finding_id}-${finding.affected_asset}-${finding.title}`}>
                      <SeverityDot severity={finding.severity} />
                      <span>{getDnsIssue(finding)}</span>
                      <span>{finding.affected_asset}</span>
                      <span>{getDnsValue(finding)}</span>
                      <span>{getDnsType(finding)}</span>
                    </div>
                  ))}
                </div>
              </div>

              <a className="card-link" href="#dns">View all DNS findings</a>
            </section>

            <aside className="right-column">
              <section className="card archive-card" id="archive">
                <div className="card-header">
                  <div>
                    <p className="eyebrow">Archive</p>
                    <h2>Local Report Archive</h2>
                  </div>
                  <button className="small-button" onClick={loadReportArchive}>Refresh</button>
                </div>

                {reportArchive.length === 0 ? (
                  <div className="empty-card">Generate a report to create the first local archive entry.</div>
                ) : (
                  <div className="archive-list">
                    {reportArchive.slice(0, 2).map((entry) => (
                      <div className="archive-row" key={entry.id}>
                        <div className="doc-icon">DOC</div>
                        <div>
                          <strong>{entry.filename}</strong>
                          <p>{entry.report_type} - {entry.format} - {formatBytes(entry.size_bytes)}</p>
                          <div className="archive-actions">
                            <button type="button" onClick={() => handleArchiveOpen(entry.id)}>Open</button>
                            <button type="button" onClick={() => handleArchiveDownload(entry.id)}>Download</button>
                            <button type="button" className="danger" onClick={() => handleArchiveDelete(entry.id)}>Delete</button>
                          </div>
                        </div>
                        <time>{formatArchiveTime(entry.generated_at_utc)}</time>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              <section className="card app-log-card" id="app-log">
                <div className="card-header">
                  <div>
                    <p className="eyebrow">Application Evidence</p>
                    <h2>App Log Evidence</h2>
                  </div>
                  <label className="button import-button">
                    <input type="file" accept=".log,.txt,.csv,.json,.ndjson,text/plain,application/json" onChange={handleAppLogImport} />
                    Import Log
                  </label>
                </div>

                <SeverityStrip counts={appLogSeverityCounts} />

                <div className="action-row">
                  <button disabled={!appLogEvidence || appLogFindings.length === 0} onClick={() => handleAppLogReportDownload("html")}>Download HTML</button>
                  <button disabled={!appLogEvidence || appLogFindings.length === 0} onClick={() => handleAppLogReportDownload("markdown")}>Download Markdown</button>
                  <button disabled={!appLogEvidence || appLogFindings.length === 0} onClick={() => handleAppLogReportDownload("json")}>Download JSON</button>
                </div>

                {appLogFileName && <p className="loaded-file">Loaded: {appLogFileName}</p>}
                {appLogWarnings.length > 0 && <p className="warning-text">{appLogWarnings.join(" | ")}</p>}

                <div className="table-panel">
                  <div className="table-title">
                    <strong>Runtime Evidence</strong>
                    <span>{appLogFindings.length} findings</span>
                  </div>

                  <div className="finding-table app-log-table">
                    <div className="table-head">
                      <span>Severity</span>
                      <span>Issue</span>
                      <span>Count</span>
                    </div>

                    {appLogFindings.slice(0, 5).map((finding) => (
                      <div className="table-row" key={`${finding.finding_id}-${finding.affected_asset}`}>
                        <SeverityDot severity={finding.severity} />
                        <span>{getAppLogIssue(finding)}</span>
                        <span>{getAppLogCount(finding)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <a className="card-link" href="#app-log">Review app log evidence</a>
              </section>
              <section className="card module-card" id="reports">
                <div className="card-header">
                  <div>
                    <p className="eyebrow">Foundation</p>
                    <h2>Modules / Foundation Status</h2>
                  </div>
                </div>

                <div className="module-list">
                  {modules.slice(0, 3).map((module) => (
                    <div className="module-row" key={module.id}>
                      <div className="module-icon">{module.name.slice(0, 2).toUpperCase()}</div>
                      <div>
                        <strong>{module.name}</strong>
                        <p>{module.description}</p>
                      </div>
                      <span className={module.status === "planned" ? "status-pill planned" : "status-pill active"}>
                        {module.status}
                      </span>
                    </div>
                  ))}
                </div>


              </section>
            </aside>
          </section>

          {(importError || reportError) && (
            <section className="alert">
              {importError || reportError}
            </section>
          )}
        </main>

        <footer className="footer-bar">
          <span><span className="dot ok" /> All systems operational</span>
          <span>Data is processed locally. Nothing leaves your network.</span>
        </footer>
      </div>
    </div>
  );
}

function KpiCard({
  icon,
  label,
  value,
  note,
  highlight = false
}: {
  icon: string;
  label: string;
  value: string;
  note: string;
  highlight?: boolean;
}) {
  return (
    <article className="kpi-card">
      <div className={highlight ? "kpi-icon highlight" : "kpi-icon"}>{icon}</div>
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
        <span>{note}</span>
      </div>
    </article>
  );
}

function SeverityStrip({ counts }: { counts: SeverityCounts }) {
  return (
    <div className="severity-strip">
      <Badge severity="critical" label="Critical" value={counts.critical} />
      <Badge severity="high" label="High" value={counts.high} />
      <Badge severity="medium" label="Medium" value={counts.medium} />
      <Badge severity="low" label="Low" value={counts.low} />
      <Badge severity="info" label="Info" value={counts.info} />
    </div>
  );
}

function Badge({ severity, label, value }: { severity: string; label: string; value: number }) {
  return (
    <span className={`severity-badge ${severity}`}>
      {label}
      <strong>{value}</strong>
    </span>
  );
}

function SeverityDot({ severity }: { severity: string }) {
  return (
    <span className={`severity-dot-row ${severity}`}>
      <i />
      {capitalize(severity)}
    </span>
  );
}

function getSeverityCounts(findings: Finding[]): SeverityCounts {
  const counts: SeverityCounts = {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    info: 0
  };

  for (const finding of findings) {
    counts[finding.severity] = (counts[finding.severity] ?? 0) + 1;
  }

  return counts;
}

function getHighestSeverity(findings: Finding[]): string {
  if (findings.length === 0) {
    return "none";
  }

  return [...findings]
    .sort(
      (a, b) =>
        SEVERITY_ORDER.indexOf(b.severity) - SEVERITY_ORDER.indexOf(a.severity)
    )[0].severity;
}

function getAffectedAsset(findings: Finding[]): string {
  if (findings.length === 0) {
    return "n/a";
  }

  return findings[0].affected_asset;
}

function normalizeEndpointEvidencePayload(payload: unknown): unknown {
  if (payload && typeof payload === "object" && "evidence" in payload) {
    const possibleReport = payload as { evidence?: unknown };

    if (possibleReport.evidence && typeof possibleReport.evidence === "object") {
      return possibleReport.evidence;
    }
  }

  return payload;
}

function getDnsModeLabel(mode: string): string {
  if (mode === "csv") {
    return "Imported DNS CSV";
  }

  if (mode === "json") {
    return "Imported DNS JSON";
  }

  return "Sample DNS evidence";
}

function getEndpointControl(finding: Finding): string {
  const id = finding.finding_id.toLowerCase();

  if (id.includes("secure_boot")) return "Secure Boot";
  if (id.includes("bitlocker")) return "BitLocker Encryption";
  if (id.includes("defender")) return "Windows Defender";
  if (id.includes("firewall")) return "Firewall Profile";
  if (id.includes("rdp")) return "Remote Desktop";
  if (id.includes("smbv1")) return "SMBv1";
  if (id.includes("reboot")) return "Pending Reboot";

  return finding.title;
}

function getEndpointStatus(finding: Finding): string {
  const firstEvidence = finding.evidence[0];

  if (!firstEvidence) {
    return "Review";
  }

  return truncate(firstEvidence.value, 18);
}

function getAppLogIssue(finding: Finding): string {
  const id = finding.finding_id.toLowerCase();

  if (id.includes("5xx")) return "HTTP server errors";
  if (id.includes("auth")) return "Auth failures";
  if (id.includes("404")) return "Repeated 404";
  if (id.includes("timeout")) return "Timeouts";
  if (id.includes("dns")) return "DNS resolution";
  if (id.includes("tls")) return "TLS/certificate";
  if (id.includes("database")) return "Database dependency";
  if (id.includes("exception")) return "Exceptions";
  if (id.includes("slow")) return "Slow requests";
  if (id.includes("sensitive")) return "Sensitive data risk";

  return finding.title;
}

function getAppLogCount(finding: Finding): string {
  const countEvidence = finding.evidence.find((item) =>
    item.key.includes("count") ||
    item.key.includes("error_count") ||
    item.key.includes("failure_count")
  );

  return countEvidence ? truncate(countEvidence.value, 10) : "n/a";
}
function getDnsIssue(finding: Finding): string {
  const id = finding.finding_id.toLowerCase();

  if (id.includes("stale")) return "DNS stale record";
  if (id.includes("ptr")) return "Reverse DNS missing";
  if (id.includes("shared_ip")) return "Multiple names same IP";
  if (id.includes("forward")) return "Forward resolution issue";

  return finding.title;
}

function getDnsValue(finding: Finding): string {
  const preferred =
    finding.evidence.find((item) => item.key.includes("ip")) ||
    finding.evidence.find((item) => item.key.includes("ptr")) ||
    finding.evidence[0];

  return preferred ? truncate(preferred.value, 20) : "n/a";
}

function getDnsType(finding: Finding): string {
  if (finding.finding_id.includes("PTR")) {
    return "PTR";
  }

  return "A";
}

function capitalize(value: string): string {
  if (!value) {
    return value;
  }

  return value.charAt(0).toUpperCase() + value.slice(1);
}

function truncate(value: string, maxLength: number): string {
  if (value.length <= maxLength) {
    return value;
  }

  return `${value.slice(0, maxLength - 1)}...`;
}

function formatBytes(value: number): string {
  if (value < 1024) {
    return `${value} B`;
  }

  if (value < 1024 * 1024) {
    return `${Math.round(value / 1024)} KB`;
  }

  return `${(value / 1024 / 1024).toFixed(1)} MB`;
}

function formatArchiveTime(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "n/a";
  }

  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
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