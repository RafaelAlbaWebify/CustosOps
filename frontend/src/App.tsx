import { ChangeEvent, useEffect, useMemo, useState } from "react";
import "./styles.css";

const API_BASE = "http://127.0.0.1:8000";

type Severity = "critical" | "high" | "medium" | "low" | "info";

type Workspace = "overview" | "endpoint" | "dns" | "app-log" | "reports" | "archive";

type ReportFormat = "html" | "markdown" | "json";

type EvidenceItem = {
  source?: string;
  key: string;
  value: string;
};

type Finding = {
  finding_id: string;
  title: string;
  severity: Severity | string;
  confidence?: string;
  category?: string;
  affected_asset?: string;
  evidence: EvidenceItem[];
  why_it_matters?: string;
  limitations?: string[];
  safe_next_steps?: string[];
  non_actions?: string[];
};

type ModuleStatus = {
  name?: string;
  module?: string;
  status?: string;
  description?: string;
};

type ArchiveEntry = {
  id: string;
  filename: string;
  report_type?: string;
  format?: string;
  content_type?: string;
  relative_path?: string;
  created_at?: string;
  size_bytes?: number;
};

type ReportResponse = {
  filename: string;
  format: string;
  content_type: string;
  content: string;
  archived?: boolean;
  archive_entry_id?: string;
};

type SeverityCounts = Record<Severity, number>;

const WORKSPACES: { id: Workspace; label: string; short: string }[] = [
  { id: "overview", label: "Overview", short: "OV" },
  { id: "endpoint", label: "Endpoint", short: "EP" },
  { id: "dns", label: "DNS Hygiene", short: "DN" },
  { id: "app-log", label: "App Logs", short: "LG" },
  { id: "reports", label: "Reports", short: "RP" },
  { id: "archive", label: "Archive", short: "AR" }
];

const DEFAULT_MODULES: ModuleStatus[] = [
  { name: "Endpoint Evidence", status: "active", description: "Local endpoint posture evidence." },
  { name: "DNS Hygiene", status: "active", description: "DNS audit JSON and CSV evidence." },
  { name: "Application Logs", status: "active", description: "Application and API runtime log evidence." },
  { name: "Reports", status: "active", description: "HTML, Markdown, and JSON evidence reports." },
  { name: "Archive", status: "active", description: "Local report archive." }
];

const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low", "info"];

function App() {
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace>(getWorkspaceFromHash());
  const [backendOnline, setBackendOnline] = useState(false);
  const [modules, setModules] = useState<ModuleStatus[]>(DEFAULT_MODULES);

  const [endpointFindings, setEndpointFindings] = useState<Finding[]>([]);
  const [endpointEvidence, setEndpointEvidence] = useState<unknown | null>(null);
  const [endpointSource, setEndpointSource] = useState("Sample endpoint evidence");
  const [endpointSelectedId, setEndpointSelectedId] = useState("");

  const [dnsFindings, setDnsFindings] = useState<Finding[]>([]);
  const [dnsEvidence, setDnsEvidence] = useState<unknown | null>(null);
  const [dnsSource, setDnsSource] = useState("Sample DNS evidence");
  const [dnsWarnings, setDnsWarnings] = useState<string[]>([]);
  const [dnsSelectedId, setDnsSelectedId] = useState("");

  const [appLogFindings, setAppLogFindings] = useState<Finding[]>([]);
  const [appLogEvidence, setAppLogEvidence] = useState<unknown | null>(null);
  const [appLogSource, setAppLogSource] = useState("");
  const [appLogWarnings, setAppLogWarnings] = useState<string[]>([]);
  const [appLogSelectedId, setAppLogSelectedId] = useState("");

  const [archiveEntries, setArchiveEntries] = useState<ArchiveEntry[]>([]);
  const [importError, setImportError] = useState("");
  const [reportError, setReportError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");

  const endpointCounts = useMemo(() => getSeverityCounts(endpointFindings), [endpointFindings]);
  const dnsCounts = useMemo(() => getSeverityCounts(dnsFindings), [dnsFindings]);
  const appLogCounts = useMemo(() => getSeverityCounts(appLogFindings), [appLogFindings]);

  const endpointSelectedFinding = endpointFindings.find((finding) => finding.finding_id === endpointSelectedId) ?? endpointFindings[0];
  const dnsSelectedFinding = dnsFindings.find((finding) => finding.finding_id === dnsSelectedId) ?? dnsFindings[0];
  const appLogSelectedFinding = appLogFindings.find((finding) => finding.finding_id === appLogSelectedId) ?? appLogFindings[0];

  const activeModuleCount = modules.filter((module) => (module.status ?? "").toLowerCase() !== "planned").length;

  useEffect(() => {
    void loadInitialData();

    const onHashChange = () => {
      setActiveWorkspace(getWorkspaceFromHash());
    };

    window.addEventListener("hashchange", onHashChange);

    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  async function loadInitialData() {
    await Promise.allSettled([
      checkBackend(),
      loadModules(),
      loadEndpointSample(),
      loadDnsSample(),
      loadReportArchive()
    ]);
  }

  async function checkBackend() {
    try {
      const response = await fetch(`${API_BASE}/api/health`);
      setBackendOnline(response.ok);
    } catch {
      setBackendOnline(false);
    }
  }

  async function loadModules() {
    try {
      const response = await fetch(`${API_BASE}/api/modules`);

      if (!response.ok) {
        return;
      }

      const data = await response.json();
      const returnedModules = Array.isArray(data.modules) ? data.modules : [];

      if (returnedModules.length > 0) {
        setModules(returnedModules);
      }
    } catch {
      setModules(DEFAULT_MODULES);
    }
  }

  async function loadEndpointSample() {
    try {
      const response = await fetch(`${API_BASE}/api/endpoint/sample-findings`);

      if (!response.ok) {
        return;
      }

      const data = await response.json();
      const findings = normalizeFindings(data.findings ?? []);

      setEndpointEvidence(data.evidence ?? null);
      setEndpointFindings(findings);
      setEndpointSelectedId(findings[0]?.finding_id ?? "");
    } catch {
      setEndpointFindings([]);
    }
  }

  async function loadDnsSample() {
    try {
      const response = await fetch(`${API_BASE}/api/dns/sample-findings`);

      if (!response.ok) {
        return;
      }

      const data = await response.json();
      const findings = normalizeFindings(data.findings ?? []);

      setDnsEvidence(data.evidence ?? null);
      setDnsFindings(findings);
      setDnsSelectedId(findings[0]?.finding_id ?? "");
    } catch {
      setDnsFindings([]);
    }
  }

  async function loadReportArchive() {
    try {
      const response = await fetch(`${API_BASE}/api/reports/archive`);

      if (!response.ok) {
        return;
      }

      const data = await response.json();
      setArchiveEntries(Array.isArray(data.reports) ? data.reports : []);
    } catch {
      setArchiveEntries([]);
    }
  }

  function navigateTo(workspace: Workspace) {
    setActiveWorkspace(workspace);
    window.location.hash = workspace;
  }

  async function handleEndpointImport(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    resetMessages();

    if (!file) {
      return;
    }

    try {
      const text = await file.text();
      const parsed = JSON.parse(text);

      if (Array.isArray(parsed.findings) && parsed.evidence) {
        const findings = normalizeFindings(parsed.findings);
        setEndpointEvidence(parsed.evidence);
        setEndpointFindings(findings);
        setEndpointSelectedId(findings[0]?.finding_id ?? "");
        setEndpointSource(file.name);
        return;
      }

      const response = await fetch(`${API_BASE}/api/endpoint/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(parsed)
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data = await response.json();
      const findings = normalizeFindings(data.findings ?? []);

      setEndpointEvidence(data.evidence ?? parsed);
      setEndpointFindings(findings);
      setEndpointSelectedId(findings[0]?.finding_id ?? "");
      setEndpointSource(file.name);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Unable to import endpoint evidence.");
    } finally {
      event.target.value = "";
    }
  }

  async function handleEndpointLocalCollect() {
    resetMessages();
    setStatusMessage("Collecting local endpoint evidence...");

    try {
      const response = await fetch(`${API_BASE}/api/endpoint/collect-local`, {
        method: "POST"
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data = await response.json();
      const findings = normalizeFindings(data.findings ?? []);

      setEndpointEvidence(data.evidence ?? data);
      setEndpointFindings(findings);
      setEndpointSelectedId(findings[0]?.finding_id ?? "");
      setEndpointSource(data.evidence_path ?? "Local endpoint collection");
      setStatusMessage("Local endpoint evidence collected.");
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Unable to collect local endpoint evidence.");
      setStatusMessage("");
    }
  }

  async function handleDnsJsonImport(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    resetMessages();

    if (!file) {
      return;
    }

    try {
      const text = await file.text();
      const parsed = JSON.parse(text);

      if (Array.isArray(parsed.findings) && parsed.evidence) {
        const findings = normalizeFindings(parsed.findings);
        setDnsEvidence(parsed.evidence);
        setDnsFindings(findings);
        setDnsSelectedId(findings[0]?.finding_id ?? "");
        setDnsSource(file.name);
        return;
      }

      const response = await fetch(`${API_BASE}/api/dns/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(parsed)
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data = await response.json();
      const findings = normalizeFindings(data.findings ?? []);

      setDnsEvidence(data.evidence ?? parsed);
      setDnsFindings(findings);
      setDnsSelectedId(findings[0]?.finding_id ?? "");
      setDnsSource(file.name);
      setDnsWarnings(data.warnings ?? []);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Unable to import DNS JSON evidence.");
    } finally {
      event.target.value = "";
    }
  }

  async function handleDnsCsvImport(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    resetMessages();

    if (!file) {
      return;
    }

    try {
      const body = new FormData();
      body.append("file", file);

      const response = await fetch(`${API_BASE}/api/dns/import-csv`, {
        method: "POST",
        body
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data = await response.json();
      const findings = normalizeFindings(data.findings ?? []);

      setDnsEvidence(data.evidence ?? null);
      setDnsFindings(findings);
      setDnsSelectedId(findings[0]?.finding_id ?? "");
      setDnsSource(file.name);
      setDnsWarnings(data.warnings ?? []);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Unable to import DNS CSV evidence.");
    } finally {
      event.target.value = "";
    }
  }

  async function handleDnsTemplateDownload() {
    resetMessages();

    try {
      const response = await fetch(`${API_BASE}/api/dns/csv-template`);

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const contentType = response.headers.get("content-type") ?? "text/csv";
      const text = await response.text();

      downloadTextFile("custosops_dns_audit_template.csv", text, contentType);
    } catch (err) {
      setReportError(err instanceof Error ? err.message : "Unable to download DNS CSV template.");
    }
  }

  async function handleAppLogImport(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    resetMessages();

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
        throw new Error(await response.text());
      }

      const data = await response.json();
      const findings = normalizeFindings(data.findings ?? []);

      setAppLogEvidence(data.evidence ?? null);
      setAppLogFindings(findings);
      setAppLogSelectedId(findings[0]?.finding_id ?? "");
      setAppLogSource(file.name);
      setAppLogWarnings(data.warnings ?? []);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Unable to import application log.");
    } finally {
      event.target.value = "";
    }
  }

  async function handleReportDownload(reportType: "endpoint" | "dns" | "app-log", format: ReportFormat) {
    resetMessages();

    const route = reportType === "app-log" ? "app-log" : reportType;
    const evidence =
      reportType === "endpoint"
        ? endpointEvidence
        : reportType === "dns"
          ? dnsEvidence
          : appLogEvidence;

    const findings =
      reportType === "endpoint"
        ? endpointFindings
        : reportType === "dns"
          ? dnsFindings
          : appLogFindings;

    if (!evidence || findings.length === 0) {
      setReportError(`No ${reportType} evidence is loaded.`);
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/reports/${route}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          evidence,
          findings,
          format,
          archive: true
        })
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data: ReportResponse = await response.json();
      downloadTextFile(data.filename, data.content, data.content_type);
      await loadReportArchive();
      setStatusMessage(`${reportType} ${format} report created and archived.`);
    } catch (err) {
      setReportError(err instanceof Error ? err.message : `Unable to create ${reportType} report.`);
    }
  }

  async function handleArchiveDelete(entry: ArchiveEntry) {
    resetMessages();

    try {
      const response = await fetch(`${API_BASE}/api/reports/archive/${entry.id}`, {
        method: "DELETE"
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      await loadReportArchive();
      setStatusMessage(`Deleted archived report: ${entry.filename}`);
    } catch (err) {
      setReportError(err instanceof Error ? err.message : "Unable to delete archived report.");
    }
  }

  function handleArchiveOpen(entry: ArchiveEntry) {
    window.open(`${API_BASE}/api/reports/archive/${entry.id}/open`, "_blank", "noopener,noreferrer");
  }

  function handleArchiveDownload(entry: ArchiveEntry) {
    window.open(`${API_BASE}/api/reports/archive/${entry.id}/download`, "_blank", "noopener,noreferrer");
  }

  function resetMessages() {
    setImportError("");
    setReportError("");
    setStatusMessage("");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">C</div>
          <strong>CustosOps</strong>
        </div>

        <nav className="workspace-nav">
          {WORKSPACES.map((workspace) => (
            <button
              className={activeWorkspace === workspace.id ? "active" : ""}
              key={workspace.id}
              onClick={() => navigateTo(workspace.id)}
              type="button"
            >
              <span>{workspace.short}</span>
              {workspace.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-card">
          <div className="mini-logo">CO</div>
          <strong>CustosOps v1.0</strong>
          <p>Cybersecurity Evidence and Posture Platform</p>
        </div>

        <button className="help-link" type="button">
          ? Help and Docs
        </button>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div>
            <p className="eyebrow">Workspace</p>
            <h1>{getWorkspaceTitle(activeWorkspace)}</h1>
          </div>

          <div className="topbar-status">
            <span className={backendOnline ? "status-dot online" : "status-dot offline"} />
            {backendOnline ? "Backend Online" : "Backend Offline"}
            <div className="avatar">AD</div>
          </div>
        </header>

        {(importError || reportError || statusMessage) && (
          <section className="message-strip">
            {importError && <div className="message error">{importError}</div>}
            {reportError && <div className="message error">{reportError}</div>}
            {statusMessage && <div className="message success">{statusMessage}</div>}
          </section>
        )}

        {activeWorkspace === "overview" && (
          <OverviewWorkspace
            endpointFindings={endpointFindings}
            dnsFindings={dnsFindings}
            appLogFindings={appLogFindings}
            archiveEntries={archiveEntries}
            endpointCounts={endpointCounts}
            dnsCounts={dnsCounts}
            appLogCounts={appLogCounts}
            activeModuleCount={activeModuleCount}
            modules={modules}
            onNavigate={navigateTo}
          />
        )}

        {activeWorkspace === "endpoint" && (
          <EvidenceWorkspace
            title="Endpoint Security Evidence"
            eyebrow="Endpoint"
            description="Review endpoint posture findings from imported or locally collected evidence."
            source={endpointSource}
            findings={endpointFindings}
            counts={endpointCounts}
            selectedFinding={endpointSelectedFinding}
            selectedId={endpointSelectedId}
            onSelect={setEndpointSelectedId}
            actions={
              <>
                <button type="button" onClick={handleEndpointLocalCollect}>Collect Local</button>
                <label className="button">
                  <input type="file" accept=".json,application/json" onChange={handleEndpointImport} />
                  Import JSON
                </label>
                <ReportButtons disabled={!endpointEvidence || endpointFindings.length === 0} onDownload={(format) => handleReportDownload("endpoint", format)} />
              </>
            }
          />
        )}

        {activeWorkspace === "dns" && (
          <EvidenceWorkspace
            title="DNS Hygiene Evidence"
            eyebrow="DNS Hygiene"
            description="Review DNS hygiene findings from JSON evidence or compatibility CSV imports."
            source={dnsSource}
            findings={dnsFindings}
            counts={dnsCounts}
            selectedFinding={dnsSelectedFinding}
            selectedId={dnsSelectedId}
            onSelect={setDnsSelectedId}
            warnings={dnsWarnings}
            actions={
              <>
                <button type="button" onClick={handleDnsTemplateDownload}>CSV Template</button>
                <label className="button">
                  <input type="file" accept=".json,application/json" onChange={handleDnsJsonImport} />
                  Import JSON
                </label>
                <label className="button success-button">
                  <input type="file" accept=".csv,text/csv" onChange={handleDnsCsvImport} />
                  Import CSV
                </label>
                <ReportButtons disabled={!dnsEvidence || dnsFindings.length === 0} onDownload={(format) => handleReportDownload("dns", format)} />
              </>
            }
          />
        )}

        {activeWorkspace === "app-log" && (
          <EvidenceWorkspace
            title="Application Log Evidence"
            eyebrow="Application Evidence"
            description="Review application and API runtime evidence: HTTP errors, auth failures, timeouts, DNS, TLS, database, exceptions, slow requests, and sensitive-data indicators."
            source={appLogSource || "No app log imported yet"}
            findings={appLogFindings}
            counts={appLogCounts}
            selectedFinding={appLogSelectedFinding}
            selectedId={appLogSelectedId}
            onSelect={setAppLogSelectedId}
            warnings={appLogWarnings}
            actions={
              <>
                <label className="button">
                  <input type="file" accept=".log,.txt,.csv,.json,.ndjson,text/plain,application/json" onChange={handleAppLogImport} />
                  Import Log
                </label>
                <ReportButtons disabled={!appLogEvidence || appLogFindings.length === 0} onDownload={(format) => handleReportDownload("app-log", format)} />
              </>
            }
          />
        )}

        {activeWorkspace === "reports" && (
          <ReportsWorkspace
            endpointReady={Boolean(endpointEvidence && endpointFindings.length)}
            dnsReady={Boolean(dnsEvidence && dnsFindings.length)}
            appLogReady={Boolean(appLogEvidence && appLogFindings.length)}
            onDownload={handleReportDownload}
          />
        )}

        {activeWorkspace === "archive" && (
          <ArchiveWorkspace
            entries={archiveEntries}
            onRefresh={loadReportArchive}
            onOpen={handleArchiveOpen}
            onDownload={handleArchiveDownload}
            onDelete={handleArchiveDelete}
          />
        )}

        <footer className="footer">
          <span className="status-dot online" />
          Data is processed locally. Nothing leaves your network.
        </footer>
      </main>
    </div>
  );
}

function OverviewWorkspace(props: {
  endpointFindings: Finding[];
  dnsFindings: Finding[];
  appLogFindings: Finding[];
  archiveEntries: ArchiveEntry[];
  endpointCounts: SeverityCounts;
  dnsCounts: SeverityCounts;
  appLogCounts: SeverityCounts;
  activeModuleCount: number;
  modules: ModuleStatus[];
  onNavigate: (workspace: Workspace) => void;
}) {
  return (
    <div className="workspace-content">
      <section className="kpi-grid">
        <KpiCard icon="EP" label="Endpoint Findings" value={String(props.endpointFindings.length)} note={getTopAsset(props.endpointFindings) || "Awaiting evidence"} />
        <KpiCard icon="DN" label="DNS Max Severity" value={capitalize(getMaxSeverity(props.dnsFindings))} note={`${props.dnsFindings.length} DNS findings`} />
        <KpiCard icon="LG" label="App Log Findings" value={String(props.appLogFindings.length)} note={getTopAsset(props.appLogFindings) || "Awaiting log import"} />
        <KpiCard icon="AR" label="Archived Reports" value={String(props.archiveEntries.length)} note="In local archive" />
      </section>

      <section className="overview-grid">
        <OverviewCard
          title="Endpoint Security Evidence"
          eyebrow="Endpoint"
          counts={props.endpointCounts}
          findings={props.endpointFindings}
          actionLabel="Open Endpoint Workspace"
          onAction={() => props.onNavigate("endpoint")}
        />

        <OverviewCard
          title="DNS Hygiene"
          eyebrow="DNS Hygiene"
          counts={props.dnsCounts}
          findings={props.dnsFindings}
          actionLabel="Open DNS Workspace"
          onAction={() => props.onNavigate("dns")}
        />

        <OverviewCard
          title="Application Log Evidence"
          eyebrow="Application Evidence"
          counts={props.appLogCounts}
          findings={props.appLogFindings}
          actionLabel="Open App Log Workspace"
          onAction={() => props.onNavigate("app-log")}
        />

        <section className="card">
          <div className="card-header">
            <div>
              <p className="eyebrow">Archive</p>
              <h2>Latest Reports</h2>
            </div>
            <button type="button" onClick={() => props.onNavigate("archive")}>Open Archive</button>
          </div>

          <div className="archive-mini-list">
            {props.archiveEntries.slice(0, 4).map((entry) => (
              <div className="archive-mini-item" key={entry.id}>
                <div className="doc-icon">DOC</div>
                <div>
                  <strong>{entry.filename}</strong>
                  <span>{entry.report_type ?? "report"} - {entry.format ?? "file"}</span>
                </div>
              </div>
            ))}

            {props.archiveEntries.length === 0 && <p className="empty-state">No archived reports yet.</p>}
          </div>
        </section>
      </section>

      <section className="card module-overview">
        <div className="card-header">
          <div>
            <p className="eyebrow">Modules</p>
            <h2>Operational Modules</h2>
          </div>
          <span className="pill">{props.activeModuleCount} active</span>
        </div>

        <div className="module-list">
          {props.modules.map((module, index) => (
            <div className="module-item" key={`${module.name ?? module.module ?? "module"}-${index}`}>
              <strong>{module.name ?? module.module ?? "Module"}</strong>
              <span>{module.description ?? module.status ?? "Available"}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function EvidenceWorkspace(props: {
  title: string;
  eyebrow: string;
  description: string;
  source: string;
  findings: Finding[];
  counts: SeverityCounts;
  selectedFinding?: Finding;
  selectedId: string;
  onSelect: (id: string) => void;
  actions: React.ReactNode;
  warnings?: string[];
}) {
  const sorted = sortFindings(props.findings);

  return (
    <div className="workspace-content">
      <section className="workspace-hero">
        <div>
          <p className="eyebrow">{props.eyebrow}</p>
          <h2>{props.title}</h2>
          <p>{props.description}</p>
          <span className="loaded-source">Loaded source: {props.source}</span>
        </div>

        <div className="workspace-actions">
          {props.actions}
        </div>
      </section>

      {props.warnings && props.warnings.length > 0 && (
        <section className="warning-panel">
          <strong>Parser warnings</strong>
          <p>{props.warnings.join(" | ")}</p>
        </section>
      )}

      <section className="severity-panel">
        <SeverityStrip counts={props.counts} />
      </section>

      <section className="workspace-grid">
        <section className="card evidence-table-card">
          <div className="card-header">
            <div>
              <p className="eyebrow">Findings</p>
              <h2>Evidence Findings</h2>
            </div>
            <span className="pill">{props.findings.length} findings</span>
          </div>

          <FindingTable
            findings={sorted}
            selectedId={props.selectedId}
            onSelect={props.onSelect}
          />
        </section>

        <FindingDetails finding={props.selectedFinding} />
      </section>
    </div>
  );
}

function ReportsWorkspace(props: {
  endpointReady: boolean;
  dnsReady: boolean;
  appLogReady: boolean;
  onDownload: (reportType: "endpoint" | "dns" | "app-log", format: ReportFormat) => void;
}) {
  return (
    <div className="workspace-content">
      <section className="workspace-hero">
        <div>
          <p className="eyebrow">Reports</p>
          <h2>Evidence Report Center</h2>
          <p>Generate local HTML, Markdown, or JSON reports from the evidence currently loaded in each module.</p>
        </div>
      </section>

      <section className="report-grid">
        <ReportCard title="Endpoint Report" ready={props.endpointReady} onDownload={(format) => props.onDownload("endpoint", format)} />
        <ReportCard title="DNS Hygiene Report" ready={props.dnsReady} onDownload={(format) => props.onDownload("dns", format)} />
        <ReportCard title="Application Log Report" ready={props.appLogReady} onDownload={(format) => props.onDownload("app-log", format)} />
      </section>
    </div>
  );
}

function ArchiveWorkspace(props: {
  entries: ArchiveEntry[];
  onRefresh: () => void;
  onOpen: (entry: ArchiveEntry) => void;
  onDownload: (entry: ArchiveEntry) => void;
  onDelete: (entry: ArchiveEntry) => void;
}) {
  return (
    <div className="workspace-content">
      <section className="workspace-hero">
        <div>
          <p className="eyebrow">Archive</p>
          <h2>Local Report Archive</h2>
          <p>Open, download, or remove reports stored in the local CustosOps archive.</p>
        </div>
        <div className="workspace-actions">
          <button type="button" onClick={props.onRefresh}>Refresh</button>
        </div>
      </section>

      <section className="card">
        <div className="archive-table">
          <div className="archive-head">
            <span>Report</span>
            <span>Type</span>
            <span>Size</span>
            <span>Actions</span>
          </div>

          {props.entries.map((entry) => (
            <div className="archive-row" key={entry.id}>
              <div className="archive-name">
                <div className="doc-icon">DOC</div>
                <div>
                  <strong>{entry.filename}</strong>
                  <span>{entry.created_at ?? entry.relative_path ?? ""}</span>
                </div>
              </div>
              <span>{entry.report_type ?? "report"} / {entry.format ?? "file"}</span>
              <span>{formatBytes(entry.size_bytes)}</span>
              <div className="row-actions">
                <button type="button" onClick={() => props.onOpen(entry)}>Open</button>
                <button type="button" onClick={() => props.onDownload(entry)}>Download</button>
                <button className="danger-button" type="button" onClick={() => props.onDelete(entry)}>Delete</button>
              </div>
            </div>
          ))}

          {props.entries.length === 0 && <p className="empty-state">No archived reports yet.</p>}
        </div>
      </section>
    </div>
  );
}

function OverviewCard(props: {
  title: string;
  eyebrow: string;
  counts: SeverityCounts;
  findings: Finding[];
  actionLabel: string;
  onAction: () => void;
}) {
  return (
    <section className="card overview-card">
      <div className="card-header">
        <div>
          <p className="eyebrow">{props.eyebrow}</p>
          <h2>{props.title}</h2>
        </div>
        <button type="button" onClick={props.onAction}>{props.actionLabel}</button>
      </div>

      <SeverityStrip counts={props.counts} />

      <div className="compact-list">
        {sortFindings(props.findings).slice(0, 5).map((finding) => (
          <div className="compact-row" key={`${finding.finding_id}-${finding.affected_asset}`}>
            <SeverityDot severity={normalizeSeverity(finding.severity)} />
            <span>{finding.title}</span>
            <em>{finding.affected_asset ?? "unknown"}</em>
          </div>
        ))}

        {props.findings.length === 0 && <p className="empty-state">No evidence loaded yet.</p>}
      </div>
    </section>
  );
}

function FindingTable(props: {
  findings: Finding[];
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="finding-table full">
      <div className="table-head">
        <span>Severity</span>
        <span>Finding</span>
        <span>Category</span>
        <span>Affected asset</span>
        <span>Confidence</span>
      </div>

      {props.findings.map((finding) => (
        <button
          className={props.selectedId === finding.finding_id ? "table-row selected" : "table-row"}
          key={`${finding.finding_id}-${finding.affected_asset}`}
          onClick={() => props.onSelect(finding.finding_id)}
          type="button"
        >
          <SeverityDot severity={normalizeSeverity(finding.severity)} />
          <span>{finding.title}</span>
          <span>{finding.category ?? "uncategorized"}</span>
          <span>{finding.affected_asset ?? "unknown"}</span>
          <span>{finding.confidence ?? "unknown"}</span>
        </button>
      ))}

      {props.findings.length === 0 && <p className="empty-state">No findings available.</p>}
    </div>
  );
}

function FindingDetails(props: { finding?: Finding }) {
  if (!props.finding) {
    return (
      <section className="card finding-detail-card">
        <div className="empty-state">Select a finding to review evidence details.</div>
      </section>
    );
  }

  const finding = props.finding;

  return (
    <section className="card finding-detail-card">
      <div className="detail-header">
        <div>
          <p className="eyebrow">Evidence Review</p>
          <h2>{finding.title}</h2>
        </div>
        <SeverityBadge severity={normalizeSeverity(finding.severity)} />
      </div>

      <div className="detail-meta">
        <span>Finding ID: {finding.finding_id}</span>
        <span>Category: {finding.category ?? "unknown"}</span>
        <span>Asset: {finding.affected_asset ?? "unknown"}</span>
        <span>Confidence: {finding.confidence ?? "unknown"}</span>
      </div>

      <DetailBlock title="Why it matters" items={finding.why_it_matters ? [finding.why_it_matters] : []} />

      <div className="detail-block">
        <h3>Evidence</h3>
        {finding.evidence.length > 0 ? (
          <div className="evidence-list">
            {finding.evidence.map((item, index) => (
              <div className="evidence-item" key={`${item.key}-${index}`}>
                <strong>{item.key}</strong>
                <code>{item.value}</code>
              </div>
            ))}
          </div>
        ) : (
          <p>No evidence items were provided for this finding.</p>
        )}
      </div>

      <DetailBlock title="Safe next steps" items={finding.safe_next_steps ?? []} />
      <DetailBlock title="Limitations" items={finding.limitations ?? []} />
      <DetailBlock title="Non-actions" items={finding.non_actions ?? []} />
    </section>
  );
}

function DetailBlock(props: { title: string; items: string[] }) {
  return (
    <div className="detail-block">
      <h3>{props.title}</h3>
      {props.items.length > 0 ? (
        <ul>
          {props.items.map((item, index) => (
            <li key={`${props.title}-${index}`}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>No details provided.</p>
      )}
    </div>
  );
}

function ReportCard(props: {
  title: string;
  ready: boolean;
  onDownload: (format: ReportFormat) => void;
}) {
  return (
    <section className="card report-card">
      <div className="card-header">
        <div>
          <p className="eyebrow">Report</p>
          <h2>{props.title}</h2>
        </div>
        <span className={props.ready ? "pill success" : "pill muted"}>{props.ready ? "Ready" : "No evidence"}</span>
      </div>

      <ReportButtons disabled={!props.ready} onDownload={props.onDownload} />
    </section>
  );
}

function ReportButtons(props: {
  disabled: boolean;
  onDownload: (format: ReportFormat) => void;
}) {
  return (
    <div className="report-buttons">
      <button disabled={props.disabled} type="button" onClick={() => props.onDownload("html")}>HTML</button>
      <button disabled={props.disabled} type="button" onClick={() => props.onDownload("markdown")}>Markdown</button>
      <button disabled={props.disabled} type="button" onClick={() => props.onDownload("json")}>JSON</button>
    </div>
  );
}

function KpiCard(props: { icon: string; label: string; value: string; note: string }) {
  return (
    <section className="kpi-card">
      <div className="kpi-icon">{props.icon}</div>
      <div>
        <span>{props.label}</span>
        <strong>{props.value}</strong>
        <p>{props.note}</p>
      </div>
    </section>
  );
}

function SeverityStrip(props: { counts: SeverityCounts }) {
  return (
    <div className="severity-strip">
      {SEVERITY_ORDER.map((severity) => (
        <span className={`severity-chip ${severity}`} key={severity}>
          {capitalize(severity)} <strong>{props.counts[severity]}</strong>
        </span>
      ))}
    </div>
  );
}

function SeverityDot(props: { severity: Severity }) {
  return (
    <span className={`severity-dot ${props.severity}`}>
      <i />
      {capitalize(props.severity)}
    </span>
  );
}

function SeverityBadge(props: { severity: Severity }) {
  return <span className={`severity-badge ${props.severity}`}>{capitalize(props.severity)}</span>;
}

function normalizeFindings(findings: Finding[]): Finding[] {
  return findings.map((finding) => ({
    ...finding,
    severity: normalizeSeverity(finding.severity),
    evidence: Array.isArray(finding.evidence) ? finding.evidence : []
  }));
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
    counts[normalizeSeverity(finding.severity)] += 1;
  }

  return counts;
}

function normalizeSeverity(value: string): Severity {
  const normalized = value.toLowerCase();

  if (normalized === "critical" || normalized === "high" || normalized === "medium" || normalized === "low" || normalized === "info") {
    return normalized;
  }

  return "info";
}

function sortFindings(findings: Finding[]): Finding[] {
  return [...findings].sort((a, b) => {
    const severityDiff = SEVERITY_ORDER.indexOf(normalizeSeverity(a.severity)) - SEVERITY_ORDER.indexOf(normalizeSeverity(b.severity));

    if (severityDiff !== 0) {
      return severityDiff;
    }

    return a.title.localeCompare(b.title);
  });
}

function getMaxSeverity(findings: Finding[]): Severity {
  if (findings.length === 0) {
    return "info";
  }

  return sortFindings(findings)[0] ? normalizeSeverity(sortFindings(findings)[0].severity) : "info";
}

function getTopAsset(findings: Finding[]): string {
  return findings.find((finding) => finding.affected_asset)?.affected_asset ?? "";
}

function getWorkspaceFromHash(): Workspace {
  const raw = window.location.hash.replace("#", "");

  if (WORKSPACES.some((workspace) => workspace.id === raw)) {
    return raw as Workspace;
  }

  return "overview";
}

function getWorkspaceTitle(workspace: Workspace): string {
  return WORKSPACES.find((item) => item.id === workspace)?.label ?? "Overview";
}

function downloadTextFile(filename: string, content: string, contentType: string) {
  const blob = new Blob([content], { type: contentType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function capitalize(value: string): string {
  return `${value.charAt(0).toUpperCase()}${value.slice(1)}`;
}

function formatBytes(value?: number): string {
  if (!value || value <= 0) {
    return "n/a";
  }

  if (value < 1024) {
    return `${value} B`;
  }

  if (value < 1024 * 1024) {
    return `${Math.round(value / 102.4) / 10} KB`;
  }

  return `${Math.round(value / 1024 / 102.4) / 10} MB`;
}

export default App;