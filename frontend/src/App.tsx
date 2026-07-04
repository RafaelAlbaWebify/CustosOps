import { ChangeEvent, useEffect, useMemo, useState } from "react";
import { apiFetch, apiUrl } from "./services/api";
import { RunHistoryWorkspace } from "./components/RunHistoryWorkspace";
import "./styles.css";

const SESSION_STORAGE_KEY = "custosops.sessionEvidence.v1";
const REVIEW_STORAGE_KEY = "custosops.findingReviews.v1";

type Severity = "critical" | "high" | "medium" | "low" | "info";

type PersistedModuleEvidence = {
  evidence: unknown | null;
  findings: Finding[];
  source: string;
  warnings?: string[];
  saved_at: string;
};

type PersistedEvidenceState = {
  endpoint?: PersistedModuleEvidence;
  dns?: PersistedModuleEvidence;
  appLog?: PersistedModuleEvidence;
  windowsEvents?: PersistedModuleEvidence;
  iis?: PersistedModuleEvidence;
};

type Workspace = "overview" | "endpoint" | "dns" | "app-log" | "windows-events" | "iis" | "reports" | "archive" | "run-history" | "redaction";

type ReportFormat = "html" | "markdown" | "json";

type ReportModule = "endpoint" | "dns" | "app-log" | "windows-events" | "iis";

type ReviewStatus = "open" | "reviewed" | "needs_follow_up" | "accepted_risk" | "false_positive";

type ReviewRecord = {
  status: ReviewStatus;
  notes: string;
  reviewed_at?: string;
  reviewed_by?: string;
};

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
  status?: ReviewStatus | string;
  review_notes?: string;
  reviewed_at?: string;
  reviewed_by?: string;
};

type ModuleStatus = {
  name?: string;
  module?: string;
  status?: string;
  description?: string;
};

type RedactionRule = {
  rule_id: string;
  label: string;
  kind: "field" | "pattern" | "literal";
  value: string;
  enabled: boolean;
  replacement: string;
  description?: string | null;
};

type RedactionSettings = {
  enabled: boolean;
  profile_name: string;
  rules: RedactionRule[];
  updated_at: string;
};

type EvidenceRun = {
  run_id: string;
  created_at: string;
  module_id: string;
  module_name: string;
  source: string;
  source_type: string;
  asset: string;
  status: "success" | "warning" | "failed";
  raw_count: number;
  parsed_count: number;
  finding_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  info_count: number;
  warning_count: number;
  report_ids: string[];
  notes?: string | null;
  metadata?: Record<string, unknown>;
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
  { id: "windows-events", label: "Windows Events", short: "WE" },
  { id: "iis", label: "IIS/Application", short: "IS" },
  { id: "reports", label: "Reports", short: "RP" },
  { id: "redaction", label: "Redaction", short: "RX" },
  { id: "run-history", label: "Run History", short: "RH" },
  { id: "archive", label: "Archive", short: "AR" }
];

const DEFAULT_MODULES: ModuleStatus[] = [
  { name: "Endpoint Evidence", status: "active", description: "Local endpoint posture evidence." },
  { name: "DNS Hygiene", status: "active", description: "DNS audit JSON and CSV evidence." },
  { name: "Application Logs", status: "active", description: "Application and API runtime log evidence." },
  { name: "Windows Event Evidence", status: "active", description: "Imported Windows Event operational evidence." },
  { name: "IIS/Application Evidence", status: "active", description: "Read-only IIS/Application local collection and report evidence." },
  { name: "Reports", status: "active", description: "HTML, Markdown, and JSON evidence reports." },
  { name: "Archive", status: "active", description: "Local report archive." }
];

const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low", "info"];

const REVIEW_OPTIONS: { value: ReviewStatus; label: string }[] = [
  { value: "open", label: "Open" },
  { value: "reviewed", label: "Reviewed" },
  { value: "needs_follow_up", label: "Needs follow-up" },
  { value: "accepted_risk", label: "Accepted risk" },
  { value: "false_positive", label: "False positive" }
];

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

  const [windowsEventFindings, setWindowsEventFindings] = useState<Finding[]>([]);
  const [windowsEventEvidence, setWindowsEventEvidence] = useState<unknown | null>(null);
  const [windowsEventSource, setWindowsEventSource] = useState("Sample Windows Event evidence");
  const [windowsEventWarnings, setWindowsEventWarnings] = useState<string[]>([]);
  const [windowsEventSelectedId, setWindowsEventSelectedId] = useState("");

  const [iisFindings, setIisFindings] = useState<Finding[]>([]);
  const [iisEvidence, setIisEvidence] = useState<unknown | null>(null);
  const [iisSource, setIisSource] = useState("Sample IIS/Application evidence");
  const [iisWarnings, setIisWarnings] = useState<string[]>([]);
  const [iisSelectedId, setIisSelectedId] = useState("");

  const [archiveEntries, setArchiveEntries] = useState<ArchiveEntry[]>([]);

  const [runHistory, setRunHistory] = useState<EvidenceRun[]>([]);

  const [redactionSettings, setRedactionSettings] = useState<RedactionSettings | null>(null);
  const [importError, setImportError] = useState("");
  const [reportError, setReportError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [reviewRecords, setReviewRecords] = useState<Record<string, ReviewRecord>>(() => loadStoredReviewRecords());

  const endpointCounts = useMemo(() => getSeverityCounts(endpointFindings), [endpointFindings]);
  const dnsCounts = useMemo(() => getSeverityCounts(dnsFindings), [dnsFindings]);
  const appLogCounts = useMemo(() => getSeverityCounts(appLogFindings), [appLogFindings]);
  const windowsEventCounts = useMemo(() => getSeverityCounts(windowsEventFindings), [windowsEventFindings]);
  const iisCounts = useMemo(() => getSeverityCounts(iisFindings), [iisFindings]);

  const endpointSelectedFinding = endpointFindings.find((finding) => finding.finding_id === endpointSelectedId) ?? endpointFindings[0];
  const dnsSelectedFinding = dnsFindings.find((finding) => finding.finding_id === dnsSelectedId) ?? dnsFindings[0];
  const appLogSelectedFinding = appLogFindings.find((finding) => finding.finding_id === appLogSelectedId) ?? appLogFindings[0];
  const windowsEventSelectedFinding = windowsEventFindings.find((finding) => finding.finding_id === windowsEventSelectedId) ?? windowsEventFindings[0];
  const iisSelectedFinding = iisFindings.find((finding) => finding.finding_id === iisSelectedId) ?? iisFindings[0];

  const activeModuleCount = modules.filter((module) => (module.status ?? "").toLowerCase() !== "planned").length;

  useEffect(() => {
    void loadInitialData();

    const onHashChange = () => {
      setActiveWorkspace(getWorkspaceFromHash());
    };

    window.addEventListener("hashchange", onHashChange);

    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem(REVIEW_STORAGE_KEY, JSON.stringify(reviewRecords));
    } catch {
      // Finding review persistence is local-only and optional.
    }
  }, [reviewRecords]);

  useEffect(() => {
    void ensureWorkspaceData(activeWorkspace);

    const retryHandle = window.setTimeout(() => {
      void ensureWorkspaceData(activeWorkspace);
    }, 1200);

    return () => window.clearTimeout(retryHandle);
  }, [activeWorkspace]);

  useEffect(() => {
    const hasPersistableEvidence =
      Boolean(endpointEvidence) ||
      Boolean(dnsEvidence) ||
      Boolean(appLogEvidence) ||
      Boolean(windowsEventEvidence) ||
      Boolean(iisEvidence) ||
      endpointFindings.length > 0 ||
      dnsFindings.length > 0 ||
      appLogFindings.length > 0 ||
      windowsEventFindings.length > 0 ||
      iisFindings.length > 0;

    if (!hasPersistableEvidence) {
      return;
    }

    const payload: PersistedEvidenceState = {
      endpoint: {
        evidence: endpointEvidence,
        findings: endpointFindings,
        source: endpointSource,
        saved_at: new Date().toISOString()
      },
      dns: {
        evidence: dnsEvidence,
        findings: dnsFindings,
        source: dnsSource,
        warnings: dnsWarnings,
        saved_at: new Date().toISOString()
      },
      appLog: {
        evidence: appLogEvidence,
        findings: appLogFindings,
        source: appLogSource,
        warnings: appLogWarnings,
        saved_at: new Date().toISOString()
      },
      windowsEvents: {
        evidence: windowsEventEvidence,
        findings: windowsEventFindings,
        source: windowsEventSource,
        warnings: windowsEventWarnings,
        saved_at: new Date().toISOString()
      },
      iis: {
        evidence: iisEvidence,
        findings: iisFindings,
        source: iisSource,
        warnings: iisWarnings,
        saved_at: new Date().toISOString()
      }
    };

    try {
      window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(payload));
    } catch {
      // Session persistence is helpful but not required for operation.
    }
  }, [
    endpointEvidence,
    endpointFindings,
    endpointSource,
    dnsEvidence,
    dnsFindings,
    dnsSource,
    dnsWarnings,
    appLogEvidence,
    appLogFindings,
    appLogSource,
    appLogWarnings,
    windowsEventEvidence,
    windowsEventFindings,
    windowsEventSource,
    windowsEventWarnings,
    iisEvidence,
    iisFindings,
    iisSource,
    iisWarnings
  ]);

  function restoreSessionEvidence(): { endpoint: boolean; dns: boolean; appLog: boolean; windowsEvents: boolean; iis: boolean } {
    const restored = {
      endpoint: false,
      dns: false,
      appLog: false,
      windowsEvents: false,
      iis: false
    };

    try {
      const raw = window.localStorage.getItem(SESSION_STORAGE_KEY);

      if (!raw) {
        return restored;
      }

      const parsed = JSON.parse(raw) as PersistedEvidenceState;

      if (parsed.endpoint?.evidence || parsed.endpoint?.findings?.length) {
        const findings = normalizeFindings(parsed.endpoint.findings ?? []);
        setEndpointEvidence(parsed.endpoint.evidence ?? null);
        setEndpointFindings(findings);
        setEndpointSelectedId(findings[0]?.finding_id ?? "");
        setEndpointSource(parsed.endpoint.source || "Restored endpoint evidence");
        restored.endpoint = true;
      }

      if (parsed.dns?.evidence || parsed.dns?.findings?.length) {
        const findings = normalizeFindings(parsed.dns.findings ?? []);
        setDnsEvidence(parsed.dns.evidence ?? null);
        setDnsFindings(findings);
        setDnsSelectedId(findings[0]?.finding_id ?? "");
        setDnsSource(parsed.dns.source || "Restored DNS evidence");
        setDnsWarnings(parsed.dns.warnings ?? []);
        restored.dns = true;
      }

      if (parsed.appLog?.evidence || parsed.appLog?.findings?.length) {
        const findings = normalizeFindings(parsed.appLog.findings ?? []);
        setAppLogEvidence(parsed.appLog.evidence ?? null);
        setAppLogFindings(findings);
        setAppLogSelectedId(findings[0]?.finding_id ?? "");
        setAppLogSource(parsed.appLog.source || "Restored application log evidence");
        setAppLogWarnings(parsed.appLog.warnings ?? []);
        restored.appLog = true;
      }

      if (parsed.windowsEvents?.evidence || parsed.windowsEvents?.findings?.length) {
        const findings = normalizeFindings(parsed.windowsEvents.findings ?? []);
        setWindowsEventEvidence(parsed.windowsEvents.evidence ?? null);
        setWindowsEventFindings(findings);
        setWindowsEventSelectedId(findings[0]?.finding_id ?? "");
        setWindowsEventSource(parsed.windowsEvents.source || "Restored Windows Event evidence");
        setWindowsEventWarnings(parsed.windowsEvents.warnings ?? []);
        restored.windowsEvents = true;
      }

      if (parsed.iis?.evidence || parsed.iis?.findings?.length) {
        const findings = normalizeFindings(parsed.iis.findings ?? []);
        setIisEvidence(parsed.iis.evidence ?? null);
        setIisFindings(findings);
        setIisSelectedId(findings[0]?.finding_id ?? "");
        setIisSource(parsed.iis.source || "Restored IIS/Application evidence");
        setIisWarnings(parsed.iis.warnings ?? []);
        restored.iis = true;
      }
    } catch {
      window.localStorage.removeItem(SESSION_STORAGE_KEY);
    }

    return restored;
  }
  async function loadInitialData() {
    const restored = restoreSessionEvidence();

    await Promise.allSettled([
      checkBackend(),
      loadModules(),
      restored.endpoint ? Promise.resolve() : loadEndpointSample(),
      restored.dns ? Promise.resolve() : loadDnsSample(),
      restored.windowsEvents ? Promise.resolve() : loadWindowsEventSample(),
      restored.iis ? Promise.resolve() : loadIisSample(),
      loadReportArchive()
    ]);
  }

  async function checkBackend() {
    try {
      const response = await apiFetch("/api/health");
      setBackendOnline(response.ok);
    } catch {
      setBackendOnline(false);
    }
  }

  async function loadModules() {
    try {
      const response = await apiFetch("/api/modules");

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
      const response = await apiFetch("/api/endpoint/sample-findings");

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
      const response = await apiFetch("/api/dns/sample-findings");

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

  async function loadWindowsEventSample() {
    try {
      const response = await apiFetch("/api/windows-events/sample-findings");

      if (!response.ok) {
        return;
      }

      const data = await response.json();
      const findings = normalizeFindings(data.findings ?? []);

      setWindowsEventEvidence(data.evidence ?? null);
      setWindowsEventFindings(findings);
      setWindowsEventSelectedId(findings[0]?.finding_id ?? "");
      setWindowsEventSource("sample-windows-events.json");
    } catch {
      setWindowsEventFindings([]);
    }
  }

  async function loadIisSample() {
    try {
      const response = await apiFetch("/api/iis/sample-findings");

      if (!response.ok) {
        return;
      }

      const data = await response.json();
      const findings = normalizeFindings(data.findings ?? []);

      setIisEvidence(data.evidence ?? null);
      setIisFindings(findings);
      setIisSelectedId(findings[0]?.finding_id ?? "");
      setIisSource("sample-iis-application-evidence.json");
      setIisWarnings(Array.isArray(data.evidence?.collection_warnings) ? data.evidence.collection_warnings.map(String) : []);
    } catch {
      setIisFindings([]);
    }
  }

  async function loadRedactionSettings() {
    try {
      const response = await apiFetch("/api/redaction/settings");

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data = await response.json();
      setRedactionSettings(data);
      setReportError("");
    } catch (err) {
      setReportError(err instanceof Error ? err.message : "Unable to load redaction settings.");
    }
  }

  async function saveRedactionSettings(settings: RedactionSettings) {
    resetMessages();

    try {
      const response = await apiFetch("/api/redaction/settings", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          enabled: settings.enabled,
          profile_name: settings.profile_name,
          rules: settings.rules
        })
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data = await response.json();
      setRedactionSettings(data);
      setReportError("");
      setStatusMessage("Redaction settings saved.");
    } catch (err) {
      setReportError(err instanceof Error ? err.message : "Unable to save redaction settings.");
    }
  }

  async function resetRedactionSettings() {
    resetMessages();

    try {
      const response = await apiFetch("/api/redaction/settings/reset", {
        method: "POST"
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data = await response.json();
      setRedactionSettings(data);
      setReportError("");
      setStatusMessage("Redaction settings reset to defaults.");
    } catch (err) {
      setReportError(err instanceof Error ? err.message : "Unable to reset redaction settings.");
    }
  }

  function updateRedactionSettings(nextSettings: RedactionSettings) {
    setRedactionSettings(nextSettings);
  }

  async function loadRunHistory() {
    try {
      const response = await apiFetch("/api/runs?limit=100");

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data = await response.json();
      setRunHistory(data.runs ?? []);
      setReportError("");
    } catch (err) {
      setReportError(err instanceof Error ? err.message : "Unable to load run history.");
    }
  }

  async function clearRunHistory() {
    resetMessages();

    try {
      const response = await apiFetch("/api/runs", {
        method: "DELETE"
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      await loadRunHistory();
      setStatusMessage("Evidence run history cleared.");
    } catch (err) {
      setReportError(err instanceof Error ? err.message : "Unable to clear run history.");
    }
  }

  async function recordEvidenceRun(input: {
    module_id: string;
    module_name: string;
    source: string;
    source_type: string;
    evidence?: unknown;
    findings: Finding[];
    raw_count?: number;
    parsed_count?: number;
    warning_count?: number;
    asset?: string;
    status?: "success" | "warning" | "failed";
    notes?: string;
    metadata?: Record<string, unknown>;
  }) {
    const warningCount = input.warning_count ?? 0;

    const payload = {
      module_id: input.module_id,
      module_name: input.module_name,
      source: input.source,
      source_type: input.source_type,
      asset: input.asset ?? inferRunAsset(input.evidence, input.findings, "unknown"),
      status: input.status ?? (warningCount > 0 ? "warning" : "success"),
      raw_count: input.raw_count ?? readNumericValue([input.evidence, input.metadata], ["raw_count", "raw_event_count", "line_count", "record_count"], 0),
      parsed_count: input.parsed_count ?? readNumericValue([input.evidence, input.metadata], ["parsed_count", "parsed_event_count", "entry_count", "record_count"], 0),
      finding_count: input.findings.length,
      high_count: countSeverity(input.findings, "high"),
      medium_count: countSeverity(input.findings, "medium"),
      low_count: countSeverity(input.findings, "low"),
      info_count: countSeverity(input.findings, "info"),
      warning_count: warningCount,
      report_ids: [],
      notes: input.notes ?? null,
      metadata: input.metadata ?? {}
    };

    try {
      const response = await apiFetch("/api/runs", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        await loadRunHistory();
      } else {
        console.warn("Unable to record evidence run:", await response.text());
      }
    } catch (err) {
      console.warn("Unable to record evidence run:", err);
    }
  }

  function countSeverity(findings: Finding[], severity: string) {
    return findings.filter((finding) => finding.severity === severity).length;
  }

  function readNumericValue(sources: unknown, keys: string[], fallback: number) {
    const candidates = Array.isArray(sources) ? sources : [sources];

    for (const candidate of candidates) {
      if (!candidate || typeof candidate !== "object") {
        continue;
      }

      const record = candidate as Record<string, unknown>;

      for (const key of keys) {
        const value = record[key];

        if (typeof value === "number" && Number.isFinite(value)) {
          return value;
        }

        if (Array.isArray(value)) {
          return value.length;
        }
      }
    }

    return fallback;
  }

  function inferRunAsset(evidence: unknown, findings: Finding[], fallback: string) {
    const affectedAsset = findings.find((finding) => finding.affected_asset)?.affected_asset;

    if (affectedAsset) {
      return affectedAsset;
    }

    if (evidence && typeof evidence === "object") {
      const record = evidence as Record<string, unknown>;
      const directAsset = record.asset ?? record.hostname ?? record.computer ?? record.computer_name ?? record.device_name;

      if (typeof directAsset === "string" && directAsset.trim()) {
        return directAsset;
      }

      const events = record.events;

      if (Array.isArray(events) && events.length > 0 && events[0] && typeof events[0] === "object") {
        const firstEvent = events[0] as Record<string, unknown>;
        const eventComputer = firstEvent.computer ?? firstEvent.hostname ?? firstEvent.asset;

        if (typeof eventComputer === "string" && eventComputer.trim()) {
          return eventComputer;
        }
      }
    }

    return fallback;
  }

  async function ensureWorkspaceData(workspace: Workspace) {
    await checkBackend();

    if (workspace === "overview") {
      await loadModules();
      return;
    }

    if (workspace === "endpoint") {
      if (!endpointEvidence && endpointFindings.length === 0) {
        await loadEndpointSample();
      }
      return;
    }

    if (workspace === "dns") {
      if (!dnsEvidence && dnsFindings.length === 0) {
        await loadDnsSample();
      }
      return;
    }

    if (workspace === "app-log") {
      // App Logs is currently import-driven. Keep explicit lifecycle coverage
      // so the workspace contract remains complete before local collection is added.
      return;
    }

    if (workspace === "windows-events") {
      if (!windowsEventEvidence && windowsEventFindings.length === 0) {
        await loadWindowsEventSample();
      }
      return;
    }

    if (workspace === "iis") {
      if (!iisEvidence && iisFindings.length === 0) {
        await loadIisSample();
      }
      return;
    }

    if (workspace === "redaction") {
      if (!redactionSettings) {
        await loadRedactionSettings();
      }
      return;
    }

    if (workspace === "run-history") {
      await loadRunHistory();
      return;
    }

    if (workspace === "reports" || workspace === "archive") {
      await loadReportArchive();
    }
  }

  async function loadReportArchive() {
    try {
      const response = await apiFetch("/api/reports/archive");

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

  function getReviewRecord(finding: Finding): ReviewRecord {
    const key = getFindingReviewKey(finding);

    return reviewRecords[key] ?? {
      status: normalizeReviewStatus(finding.status),
      notes: finding.review_notes ?? "",
      reviewed_at: finding.reviewed_at,
      reviewed_by: finding.reviewed_by
    };
  }

  function updateFindingReview(finding: Finding, status: ReviewStatus, notes: string) {
    const key = getFindingReviewKey(finding);

    setReviewRecords((current) => ({
      ...current,
      [key]: {
        status,
        notes,
        reviewed_at: new Date().toISOString(),
        reviewed_by: "local-operator"
      }
    }));
  }

  function applyReviewsToFindings(findings: Finding[]): Finding[] {
    return findings.map((finding) => {
      const review = getReviewRecord(finding);

      return {
        ...finding,
        status: review.status,
        review_notes: review.notes,
        reviewed_at: review.reviewed_at,
        reviewed_by: review.reviewed_by
      };
    });
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

      const response = await apiFetch("/api/endpoint/analyze", {
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

      await recordEvidenceRun({
        module_id: "endpoint",
        module_name: "Endpoint Security",
        source: file.name,
        source_type: "endpoint_import",
        evidence: data.evidence ?? data,
        findings,
        raw_count: 1,
        parsed_count: 1
      });
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
      const response = await apiFetch("/api/endpoint/collect-local", {
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

      await recordEvidenceRun({
        module_id: "endpoint",
        module_name: "Endpoint Security",
        source: data.evidence_path ?? "Local endpoint collection",
        source_type: "endpoint_local_collection",
        evidence: data.evidence ?? data,
        findings,
        raw_count: 1,
        parsed_count: 1
      });
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

      const response = await apiFetch("/api/dns/analyze", {
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

      await recordEvidenceRun({
        module_id: "dns",
        module_name: "DNS Hygiene",
        source: file.name,
        source_type: "dns_import",
        evidence: data.evidence ?? data,
        findings,
        raw_count: readNumericValue([data.evidence, data], ["raw_count", "record_count", "total_records"], findings.length),
        parsed_count: readNumericValue([data.evidence, data], ["parsed_count", "record_count", "total_records"], findings.length),
        warning_count: (data.warnings ?? []).length
      });
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

      const response = await apiFetch("/api/dns/import-csv", {
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

      await recordEvidenceRun({
        module_id: "dns",
        module_name: "DNS Hygiene",
        source: file.name,
        source_type: "dns_import",
        evidence: data.evidence ?? data,
        findings,
        raw_count: readNumericValue([data.evidence, data], ["raw_count", "record_count", "total_records"], findings.length),
        parsed_count: readNumericValue([data.evidence, data], ["parsed_count", "record_count", "total_records"], findings.length),
        warning_count: (data.warnings ?? []).length
      });
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Unable to import DNS CSV evidence.");
    } finally {
      event.target.value = "";
    }
  }

  async function handleDnsTemplateDownload() {
    resetMessages();

    try {
      const response = await apiFetch("/api/dns/csv-template");

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

      const response = await apiFetch("/api/app-log/import", {
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

      await recordEvidenceRun({
        module_id: "app-logs",
        module_name: "Application Logs",
        source: file.name,
        source_type: "app_log_import",
        evidence: data.evidence ?? data,
        findings,
        raw_count: readNumericValue([data.evidence, data], ["raw_count", "line_count", "entry_count", "record_count"], findings.length),
        parsed_count: readNumericValue([data.evidence, data], ["parsed_count", "entry_count", "record_count"], findings.length),
        warning_count: (data.warnings ?? []).length
      });
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Unable to import application log.");
    } finally {
      event.target.value = "";
    }
  }

  async function handleWindowsEventCollectLocal() {
    resetMessages();

    try {
      const response = await apiFetch("/api/windows-events/collect-local", {
        method: "POST"
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data = await response.json();
      const findings = normalizeFindings(data.findings ?? []);

      setWindowsEventEvidence(data.evidence ?? null);
      setWindowsEventFindings(findings);
      setWindowsEventSelectedId(findings[0]?.finding_id ?? "");
      setWindowsEventSource(data.output_path ? `Local collection: ${data.output_path}` : "Local Windows Event collection");
      setWindowsEventWarnings(data.warnings ?? []);
      setStatusMessage(`Local Windows Event collection completed. Events parsed: ${data.parsed_event_count ?? 0}. Findings: ${findings.length}.`);

      await recordEvidenceRun({
        module_id: "windows-events",
        module_name: "Windows Events",
        source: data.output_path ? `Local collection: ${data.output_path}` : "Local Windows Event collection",
        source_type: "windows_event_log_local_collection",
        evidence: data.evidence ?? data,
        findings,
        raw_count: readNumericValue([data.evidence, data], ["raw_event_count", "raw_count"], 0),
        parsed_count: readNumericValue([data.evidence, data], ["parsed_event_count", "parsed_count"], data.parsed_event_count ?? 0),
        warning_count: (data.warnings ?? []).length,
        asset: typeof data.asset === "string" && data.asset.trim() ? data.asset : inferRunAsset(data.evidence ?? data, findings, "local-host"),
        status: "success",
        notes: findings.length === 0 ? "Local Windows Event collection completed with no findings." : undefined,
        metadata: {
          output_path: data.output_path ?? null,
          parser_warnings: data.warnings ?? []
        }
      });
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Unable to collect local Windows Event evidence.");
    }
  }

  async function handleWindowsEventImport(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    resetMessages();

    if (!file) {
      return;
    }

    try {
      const text = await file.text();

      const response = await apiFetch("/api/windows-events/import", {
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

      setWindowsEventEvidence(data.evidence ?? null);
      setWindowsEventFindings(findings);
      setWindowsEventSelectedId(findings[0]?.finding_id ?? "");
      setWindowsEventSource(file.name);
      setWindowsEventWarnings(data.warnings ?? []);

      await recordEvidenceRun({
        module_id: "windows-events",
        module_name: "Windows Events",
        source: file.name,
        source_type: "windows_event_import",
        evidence: data.evidence ?? data,
        findings,
        raw_count: readNumericValue([data.evidence, data], ["raw_event_count", "raw_count"], findings.length),
        parsed_count: readNumericValue([data.evidence, data], ["parsed_event_count", "parsed_count"], findings.length),
        warning_count: (data.warnings ?? []).length
      });
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Unable to import Windows Event evidence.");
    } finally {
      event.target.value = "";
    }
  }

  async function handleIisCollectLocal() {
    resetMessages();

    try {
      const response = await apiFetch("/api/iis/collect-local", {
        method: "POST"
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data = await response.json();
      const findings = normalizeFindings(data.findings ?? []);
      const warnings = Array.isArray(data.warnings) ? data.warnings.map(String) : [];

      setIisEvidence(data.evidence ?? null);
      setIisFindings(findings);
      setIisSelectedId(findings[0]?.finding_id ?? "");
      setIisSource("Local IIS/Application collection");
      setIisWarnings(warnings);
      setStatusMessage(`Local IIS/Application collection loaded: ${findings.length} findings.`);

      await recordEvidenceRun({
        module_id: "iis",
        module_name: "IIS/Application Evidence",
        source: "Local IIS/Application collection",
        source_type: data.input_type ?? "local_iis_application_collection",
        evidence: data.evidence,
        findings,
        raw_count: data.raw_item_count,
        parsed_count: data.parsed_item_count,
        warning_count: warnings.length,
        asset: data.asset,
        notes: warnings.length > 0 ? warnings.join(" | ") : undefined,
        metadata: {
          action: "collect-local"
        }
      });
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Unable to collect local IIS/Application evidence.");
    }
  }

  async function handleIisJsonImport(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    resetMessages();

    if (!file) {
      return;
    }

    try {
      const text = await file.text();
      const response = await apiFetch("/api/iis/import", {
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
      const warnings = Array.isArray(data.warnings) ? data.warnings.map(String) : [];

      setIisEvidence(data.evidence ?? null);
      setIisFindings(findings);
      setIisSelectedId(findings[0]?.finding_id ?? "");
      setIisSource(file.name);
      setIisWarnings(warnings);
      setStatusMessage(`IIS/Application evidence imported: ${findings.length} findings.`);

      await recordEvidenceRun({
        module_id: "iis",
        module_name: "IIS/Application Evidence",
        source: file.name,
        source_type: data.input_type ?? "iis_application_import",
        evidence: data.evidence,
        findings,
        raw_count: data.raw_item_count,
        parsed_count: data.parsed_item_count,
        warning_count: warnings.length,
        asset: data.asset,
        notes: warnings.length > 0 ? warnings.join(" | ") : undefined,
        metadata: {
          action: "import-json"
        }
      });
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Unable to import IIS/Application evidence.");
    } finally {
      event.target.value = "";
    }
  }

  function buildExecutiveSummaryModules(): Array<{
    module_id: string;
    module_name: string;
    source: string;
    evidence: Record<string, unknown>;
    findings: Finding[];
  }> {
    const modules: Array<{
      module_id: string;
      module_name: string;
      source: string;
      evidence: Record<string, unknown>;
      findings: Finding[];
    }> = [];

    const reviewedEndpointFindings = applyReviewsToFindingsForReport(endpointFindings, reviewRecords);
    const reviewedDnsFindings = applyReviewsToFindingsForReport(dnsFindings, reviewRecords);
    const reviewedAppLogFindings = applyReviewsToFindingsForReport(appLogFindings, reviewRecords);
    const reviewedWindowsEventFindings = applyReviewsToFindingsForReport(windowsEventFindings, reviewRecords);
    const reviewedIisFindings = applyReviewsToFindingsForReport(iisFindings, reviewRecords);

    if (reviewedEndpointFindings.length > 0) {
      modules.push({
        module_id: "endpoint",
        module_name: "Endpoint Security",
        source: endpointSource || "Endpoint evidence",
        evidence: buildReportEvidence("endpoint", endpointEvidence, reviewedEndpointFindings),
        findings: reviewedEndpointFindings
      });
    }

    if (reviewedDnsFindings.length > 0) {
      modules.push({
        module_id: "dns",
        module_name: "DNS Hygiene",
        source: dnsSource || "DNS evidence",
        evidence: buildReportEvidence("dns", dnsEvidence, reviewedDnsFindings),
        findings: reviewedDnsFindings
      });
    }

    if (reviewedAppLogFindings.length > 0) {
      modules.push({
        module_id: "app-log",
        module_name: "Application Logs",
        source: appLogSource || "Application log evidence",
        evidence: buildReportEvidence("app-log", appLogEvidence, reviewedAppLogFindings),
        findings: reviewedAppLogFindings
      });
    }

    if (reviewedWindowsEventFindings.length > 0) {
      modules.push({
        module_id: "windows-events",
        module_name: "Windows Event Evidence",
        source: windowsEventSource || "Windows Event evidence",
        evidence: buildReportEvidence("windows-events", windowsEventEvidence, reviewedWindowsEventFindings),
        findings: reviewedWindowsEventFindings
      });
    }

    if (reviewedIisFindings.length > 0) {
      modules.push({
        module_id: "iis",
        module_name: "IIS/Application Evidence",
        source: iisSource || "IIS/Application evidence",
        evidence: buildReportEvidence("iis", iisEvidence, reviewedIisFindings),
        findings: reviewedIisFindings
      });
    }

    return modules;
  }

  function applyReviewsToFindingsForReport(findings: Finding[], records: Record<string, ReviewRecord>): Finding[] {
    return findings.map((finding) => {
      const review = records[getFindingReviewKey(finding)];

      if (!review) {
        return finding;
      }

      return {
        ...finding,
        status: review.status,
        review_notes: review.notes,
        reviewed_at: review.reviewed_at,
        reviewed_by: review.reviewed_by
      };
    });
  }

  async function handleExecutiveSummaryDownload(format: ReportFormat) {
    resetMessages();

    const modules = buildExecutiveSummaryModules();

    if (modules.length === 0) {
      setReportError("No evidence findings are currently loaded for the executive summary.");
      return;
    }

    try {
      const response = await apiFetch("/api/reports/executive-summary", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          modules,
          format,
          archive: true
        })
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data = await response.json();

      downloadTextFile(data.filename, data.content, data.content_type);
      setStatusMessage(`Executive Summary Pack generated: ${data.filename}`);

      await loadReportArchive();
    loadRunHistory();
    } catch (err) {
      setReportError(err instanceof Error ? err.message : "Unable to generate Executive Summary Pack.");
    }
  }

  async function handleReportDownload(reportType: ReportModule, format: ReportFormat) {
    resetMessages();

    const route = reportType;

    const evidence =
      reportType === "endpoint"
        ? endpointEvidence
        : reportType === "dns"
          ? dnsEvidence
          : reportType === "app-log"
            ? appLogEvidence
            : reportType === "windows-events"
              ? windowsEventEvidence
              : iisEvidence;

    const findings =
      reportType === "endpoint"
        ? endpointFindings
        : reportType === "dns"
          ? dnsFindings
          : reportType === "app-log"
            ? appLogFindings
            : reportType === "windows-events"
              ? windowsEventFindings
              : iisFindings;

    const hasReportEvidence = Boolean(evidence) || findings.length > 0;

    if (!hasReportEvidence) {
      setReportError(`No ${reportType} evidence is loaded.`);
      return;
    }

    const reportFindings = applyReviewsToFindings(findings);
    const reportEvidence = buildReportEvidence(reportType, evidence, reportFindings);

    try {
      const response = await apiFetch(`/api/reports/${route}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          evidence: reportEvidence,
          findings: reportFindings,
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
      const response = await apiFetch(`/api/reports/archive/${entry.id}`, {
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
    window.open(apiUrl(`/api/reports/archive/${entry.id}/open`), "_blank", "noopener,noreferrer");
  }

  function handleArchiveDownload(entry: ArchiveEntry) {
    window.open(apiUrl(`/api/reports/archive/${entry.id}/download`), "_blank", "noopener,noreferrer");
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
            iisFindings={iisFindings}
            archiveEntries={archiveEntries}
            endpointCounts={endpointCounts}
            dnsCounts={dnsCounts}
            appLogCounts={appLogCounts}
            iisCounts={iisCounts}
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
            reviewRecord={endpointSelectedFinding ? getReviewRecord(endpointSelectedFinding) : undefined}
            onReviewChange={updateFindingReview}
            actions={
              <>
                <button type="button" onClick={handleEndpointLocalCollect}>Collect Local</button>
                <label className="button">
                  <input type="file" accept=".json,application/json" onChange={handleEndpointImport} />
                  Import JSON
                </label>
                <ReportButtons disabled={!endpointEvidence} onDownload={(format) => handleReportDownload("endpoint", format)} />
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
            reviewRecord={dnsSelectedFinding ? getReviewRecord(dnsSelectedFinding) : undefined}
            onReviewChange={updateFindingReview}
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
                <ReportButtons disabled={!dnsEvidence} onDownload={(format) => handleReportDownload("dns", format)} />
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
            reviewRecord={appLogSelectedFinding ? getReviewRecord(appLogSelectedFinding) : undefined}
            onReviewChange={updateFindingReview}
            warnings={appLogWarnings}
            actions={
              <>
                <label className="button">
                  <input type="file" accept=".log,.txt,.csv,.json,.ndjson,text/plain,application/json" onChange={handleAppLogImport} />
                  Import Log
                </label>
                <ReportButtons disabled={!appLogEvidence} onDownload={(format) => handleReportDownload("app-log", format)} />
              </>
            }
          />
        )}

        {activeWorkspace === "windows-events" && (
          <EvidenceWorkspace
            title="Windows Event Evidence"
            eyebrow="Windows Events"
            description="Review imported Windows Event evidence: service failures, failed logons, application errors, DNS client events, and reboot/update timeline signals."
            source={windowsEventSource}
            findings={windowsEventFindings}
            counts={windowsEventCounts}
            selectedFinding={windowsEventSelectedFinding}
            selectedId={windowsEventSelectedId}
            onSelect={setWindowsEventSelectedId}
            reviewRecord={windowsEventSelectedFinding ? getReviewRecord(windowsEventSelectedFinding) : undefined}
            onReviewChange={updateFindingReview}
            warnings={windowsEventWarnings}
            actions={
              <>
                <button type="button" className="button" onClick={handleWindowsEventCollectLocal}>
                  Collect Local
                </button>
                <label className="button">
                  <input type="file" accept=".json,.csv,application/json,text/csv" onChange={handleWindowsEventImport} />
                  Import JSON/CSV
                </label>
                <ReportButtons disabled={!windowsEventEvidence} onDownload={(format) => handleReportDownload("windows-events", format)} />
              </>
            }
          />
        )}

        {activeWorkspace === "iis" && (
          <EvidenceWorkspace
            title="IIS/Application Evidence"
            eyebrow="IIS/Application"
            description="Review local IIS/Application evidence: IIS service state, sites, application pools, applications, log visibility, and collection warnings. Missing IIS is treated as a valid zero-evidence state."
            source={iisSource}
            findings={iisFindings}
            counts={iisCounts}
            selectedFinding={iisSelectedFinding}
            selectedId={iisSelectedId}
            onSelect={setIisSelectedId}
            reviewRecord={iisSelectedFinding ? getReviewRecord(iisSelectedFinding) : undefined}
            onReviewChange={updateFindingReview}
            warnings={iisWarnings}
            actions={
              <>
                <button type="button" className="button" onClick={handleIisCollectLocal}>
                  Collect Local
                </button>
                <label className="button">
                  <input type="file" accept=".json,application/json" onChange={handleIisJsonImport} />
                  Import JSON
                </label>
                <ReportButtons disabled={!iisEvidence} onDownload={(format) => handleReportDownload("iis", format)} />
              </>
            }
          />
        )}

        {activeWorkspace === "redaction" && (
          <RedactionSettingsWorkspace
            settings={redactionSettings}
            onChange={updateRedactionSettings}
            onSave={saveRedactionSettings}
            onReset={resetRedactionSettings}
            onRefresh={loadRedactionSettings}
          />
        )}

        {activeWorkspace === "run-history" && (
          <RunHistoryWorkspace runs={runHistory} onRefresh={loadRunHistory} onClear={clearRunHistory} />
        )}

        {activeWorkspace === "reports" && (
          <ReportsWorkspace
            endpointReady={endpointFindings.length > 0}
            dnsReady={dnsFindings.length > 0}
            appLogReady={appLogFindings.length > 0}
            windowsEventReady={Boolean(windowsEventEvidence)}
            iisReady={Boolean(iisEvidence)}
            executiveReady={Boolean(endpointEvidence) || Boolean(dnsEvidence) || Boolean(appLogEvidence) || Boolean(windowsEventEvidence) || Boolean(iisEvidence)}
            onDownload={handleReportDownload}
            onExecutiveDownload={handleExecutiveSummaryDownload}
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
  iisFindings: Finding[];
  archiveEntries: ArchiveEntry[];
  endpointCounts: SeverityCounts;
  dnsCounts: SeverityCounts;
  appLogCounts: SeverityCounts;
  iisCounts: SeverityCounts;
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
        <KpiCard icon="IS" label="IIS Findings" value={String(props.iisFindings.length)} note={getTopAsset(props.iisFindings) || "Awaiting IIS collection"} />
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

        <OverviewCard
          title="IIS/Application Evidence"
          eyebrow="IIS/Application"
          counts={props.iisCounts}
          findings={props.iisFindings}
          actionLabel="Open IIS Workspace"
          onAction={() => props.onNavigate("iis")}
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
  reviewRecord?: ReviewRecord;
  onReviewChange?: (finding: Finding, status: ReviewStatus, notes: string) => void;
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

        <FindingDetails finding={props.selectedFinding} reviewRecord={props.reviewRecord} onReviewChange={props.onReviewChange} />
      </section>
    </div>
  );
}

function RedactionSettingsWorkspace(props: {
  settings: RedactionSettings | null;
  onChange: (settings: RedactionSettings) => void;
  onSave: (settings: RedactionSettings) => void;
  onReset: () => void;
  onRefresh: () => void;
}) {
  const [previewText, setPreviewText] = useState("Contact analyst@example.com from C:\\Users\\analyst\\Desktop");
  const [previewResult, setPreviewResult] = useState<{ redacted: string; changed: boolean; applied_rules: string[] } | null>(null);
  const [previewStatus, setPreviewStatus] = useState("");

  async function runRedactionPreview() {
    setPreviewStatus("");
    setPreviewResult(null);

    try {
      const response = await apiFetch("/api/redaction/preview", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          text: previewText
        })
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data = await response.json();

      setPreviewResult({
        redacted: String(data.redacted ?? ""),
        changed: Boolean(data.changed),
        applied_rules: Array.isArray(data.applied_rules) ? data.applied_rules.map(String) : []
      });
    } catch (err) {
      setPreviewStatus(err instanceof Error ? err.message : "Unable to preview redaction.");
    }
  }

  if (!props.settings) {
    return (
      <section className="workspace">
        <div className="workspace-header">
          <div>
            <p className="eyebrow">Redaction controls</p>
            <h2>Redaction Settings</h2>
            <p className="muted">Loading local redaction settings...</p>
          </div>
          <div className="actions">
            <button type="button" className="button secondary" onClick={props.onRefresh}>
              Refresh
            </button>
          </div>
        </div>
      </section>
    );
  }

  const enabledRules = props.settings.rules.filter((rule) => rule.enabled).length;

  function updateProfileName(profileName: string) {
    props.onChange({
      ...props.settings!,
      profile_name: profileName
    });
  }

  function updateGlobalEnabled(enabled: boolean) {
    props.onChange({
      ...props.settings!,
      enabled
    });
  }

  function updateRule(ruleId: string, updates: Partial<RedactionRule>) {
    props.onChange({
      ...props.settings!,
      rules: props.settings!.rules.map((rule) =>
        rule.rule_id === ruleId
          ? {
              ...rule,
              ...updates
            }
          : rule
      )
    });
  }

  return (
    <section className="workspace">
      <div className="workspace-header">
        <div>
          <p className="eyebrow">Redaction controls</p>
          <h2>Redaction Settings</h2>
          <p className="muted">
            Configure local redaction preferences. These settings are stored locally and are applied to generated reports.
          </p>
        </div>
        <div className="actions">
          <button type="button" className="button secondary" onClick={props.onRefresh}>
            Refresh
          </button>
          <button type="button" className="button secondary" onClick={props.onReset}>
            Reset Defaults
          </button>
          <button type="button" className="button" onClick={() => props.onSave(props.settings!)}>
            Save Settings
          </button>
        </div>
      </div>

      <div className="metric-grid">
        <div className="metric-card">
          <span>Profile</span>
          <strong>{props.settings.profile_name}</strong>
        </div>
        <div className="metric-card">
          <span>Redaction</span>
          <strong>{props.settings.enabled ? "Enabled" : "Disabled"}</strong>
        </div>
        <div className="metric-card">
          <span>Enabled rules</span>
          <strong>{enabledRules}</strong>
        </div>
        <div className="metric-card">
          <span>Total rules</span>
          <strong>{props.settings.rules.length}</strong>
        </div>
      </div>

      <div className="panel redaction-panel">
        <div className="form-grid">
          <label>
            Profile name
            <input
              type="text"
              value={props.settings.profile_name}
              onChange={(event) => updateProfileName(event.target.value)}
            />
          </label>

          <label className="toggle-row">
            <input
              type="checkbox"
              checked={props.settings.enabled}
              onChange={(event) => updateGlobalEnabled(event.target.checked)}
            />
            Enable redaction profile
          </label>
        </div>

        <p className="muted">
          Updated: {formatRunDate(props.settings.updated_at)}
        </p>
      </div>

      <div className="panel redaction-preview-panel">
        <div className="workspace-header compact-header">
          <div>
            <p className="eyebrow">Preview</p>
            <h3>Preview redaction</h3>
            <p className="muted">
              Test the current local redaction profile before using it in generated reports.
            </p>
          </div>
          <div className="actions">
            <button type="button" className="button" onClick={runRedactionPreview}>
              Preview Redaction
            </button>
          </div>
        </div>

        <div className="preview-grid">
          <label>
            Original text
            <textarea
              value={previewText}
              onChange={(event) => setPreviewText(event.target.value)}
              rows={6}
            />
          </label>

          <label>
            Redacted preview
            <textarea
              value={previewResult?.redacted ?? ""}
              readOnly
              rows={6}
              placeholder="Preview output will appear here."
            />
          </label>
        </div>

        {previewResult && (
          <div className="preview-result">
            <p className="muted">
              Changed: <strong>{previewResult.changed ? "yes" : "no"}</strong>
            </p>
            <p className="muted">
              Applied rules: {previewResult.applied_rules.length > 0 ? previewResult.applied_rules.join(", ") : "none"}
            </p>
          </div>
        )}

        {previewStatus && <p className="error-text">{previewStatus}</p>}
      </div>

      <div className="redaction-rule-grid">
        {props.settings.rules.map((rule) => (
          <article className="redaction-rule-card" key={rule.rule_id}>
            <div className="rule-card-top">
              <div>
                <p className="eyebrow">{rule.kind}</p>
                <h3>{rule.label}</h3>
                <p className="muted">{rule.description ?? "No description provided."}</p>
              </div>
              <label className="toggle-row compact">
                <input
                  type="checkbox"
                  checked={rule.enabled}
                  onChange={(event) => updateRule(rule.rule_id, { enabled: event.target.checked })}
                />
                Enabled
              </label>
            </div>

            <dl className="rule-details">
              <div>
                <dt>Rule ID</dt>
                <dd><code>{rule.rule_id}</code></dd>
              </div>
              <div>
                <dt>Matcher</dt>
                <dd><code>{rule.value}</code></dd>
              </div>
            </dl>

            <label>
              Replacement
              <input
                type="text"
                value={rule.replacement}
                onChange={(event) => updateRule(rule.rule_id, { replacement: event.target.value })}
              />
            </label>
          </article>
        ))}
      </div>
    </section>
  );
}

function formatRunDate(value: string) {
  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString();
}

function ReportsWorkspace(props: {
  endpointReady: boolean;
  dnsReady: boolean;
  appLogReady: boolean;
  windowsEventReady: boolean;
  iisReady: boolean;
  executiveReady: boolean;
  onDownload: (reportType: ReportModule, format: ReportFormat) => void;
  onExecutiveDownload: (format: ReportFormat) => void;
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
        <ReportCard title="Windows Event Report" ready={props.windowsEventReady} onDownload={(format) => props.onDownload("windows-events", format)} />
        <ReportCard title="IIS/Application Report" ready={props.iisReady} onDownload={(format) => props.onDownload("iis", format)} />
        <ReportCard title="Executive Summary Pack" ready={props.executiveReady} onDownload={props.onExecutiveDownload} />
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

function FindingDetails(props: { finding?: Finding; reviewRecord?: ReviewRecord; onReviewChange?: (finding: Finding, status: ReviewStatus, notes: string) => void }) {
  if (!props.finding) {
    return (
      <section className="card finding-detail-card">
        <div className="empty-state">Select a finding to review evidence details.</div>
      </section>
    );
  }

  const finding = props.finding;
  const review = props.reviewRecord ?? {
    status: normalizeReviewStatus(finding.status),
    notes: finding.review_notes ?? "",
    reviewed_at: finding.reviewed_at,
    reviewed_by: finding.reviewed_by
  };

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

      <div className="review-panel">
        <h3>Operator review</h3>
        <div className="review-grid">
          <label>
            Status
            <select
              value={review.status}
              onChange={(event) => props.onReviewChange?.(finding, normalizeReviewStatus(event.target.value), review.notes)}
            >
              {REVIEW_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>

          <label>
            Notes
            <textarea
              value={review.notes}
              onChange={(event) => props.onReviewChange?.(finding, review.status, event.target.value)}
              placeholder="Add local review notes for this finding."
              rows={3}
            />
          </label>
        </div>
        <p className="review-meta">
          {review.reviewed_at ? `Last reviewed: ${review.reviewed_at}` : "Not reviewed yet"}
        </p>
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

function getFindingReviewKey(finding: Finding): string {
  return `${finding.finding_id}::${finding.affected_asset ?? "unknown"}`;
}

function loadStoredReviewRecords(): Record<string, ReviewRecord> {
  try {
    const raw = window.localStorage.getItem(REVIEW_STORAGE_KEY);

    if (!raw) {
      return {};
    }

    const parsed = JSON.parse(raw) as Record<string, ReviewRecord>;

    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function normalizeReviewStatus(value: unknown): ReviewStatus {
  const raw = String(value ?? "open");

  if (raw === "reviewed" || raw === "needs_follow_up" || raw === "accepted_risk" || raw === "false_positive") {
    return raw;
  }

  return "open";
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

function buildEvidenceFallback(reportType: "endpoint" | "dns" | "app-log", findings: Finding[]): Record<string, unknown> {
  return {
    source_type: `${reportType}_session_evidence`,
    source_file: "custosops-session",
    generated_from: "loaded findings",
    finding_count: findings.length,
    note: "Raw evidence was not available in frontend state, so CustosOps generated a minimal evidence metadata object for report continuity."
  };
}
function buildReportEvidence(reportType: ReportModule, evidence: unknown | null, findings: Finding[]): Record<string, unknown> {
  const base: Record<string, unknown> = isRecord(evidence) ? { ...evidence } : {};
  const topAsset = getTopAsset(findings) || "session-evidence";

  if (!base.source_type) {
    base.source_type = `${reportType}_session_evidence`;
  }

  if (!base.generated_from) {
    base.generated_from = "loaded findings";
  }

  base.finding_count = findings.length;

  if (reportType === "endpoint") {
    if (!base.endpoint_name && !base.hostname && !base.computer_name && !base.device_name) {
      base.endpoint_name = topAsset;
      base.hostname = topAsset;
      base.computer_name = topAsset;
    }

    if (!base.source_file || base.source_file === "custosops-session" || base.source_file === "unknown-endpoint") {
      base.source_file = topAsset;
    }
  }

  if (reportType === "dns") {
    if (!base.source_file || base.source_file === "custosops-session") {
      base.source_file = "restored-dns-session";
    }

    if (!Array.isArray(base.records) && !Array.isArray(base.dns_records)) {
      const assets = Array.from(
        new Set(
          findings
            .map((finding) => finding.affected_asset)
            .filter((asset): asset is string => Boolean(asset))
        )
      );

      base.records = assets.map((asset) => ({
        host_name: asset,
        record_type: "A",
        raw: {
          source: "loaded findings",
          record: asset
        }
      }));
    }
  }

  if (reportType === "app-log") {
    if (!base.source_file) {
      base.source_file = topAsset || "app-log";
    }
  }

  if (reportType === "windows-events") {
    if (!base.source_file) {
      base.source_file = topAsset || "windows-events";
    }

    if (!base.source_type) {
      base.source_type = "windows_event_session_evidence";
    }
  }

  if (reportType === "iis") {
    if (!base.source_file) {
      base.source_file = topAsset || "iis-application";
    }

    if (!base.asset) {
      base.asset = topAsset;
    }

    if (!base.source_type || base.source_type === "iis_session_evidence") {
      base.source_type = "iis_application_session_evidence";
    }
  }

  return base;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
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