import { apiFetch } from "./services/api";
import "./gui-fixes.css";

type ReportFormat = "html" | "markdown" | "json";

type Finding = {
  finding_id: string;
  title: string;
  severity: string;
  confidence?: string;
  category?: string;
  affected_asset?: string;
  evidence?: unknown[];
  why_it_matters?: string;
  limitations?: string[];
  safe_next_steps?: string[];
  non_actions?: string[];
};

type RiskySigninSample = {
  evidence: Record<string, unknown> | null;
  findings: Finding[];
};

type EvidenceRun = {
  created_at: string;
  module_name: string;
  source_type: string;
  asset: string;
  source: string;
  status: "success" | "warning" | "failed";
  finding_count: number;
};

type ArchiveEntry = {
  filename: string;
  created_at?: string;
  format?: string;
  report_type?: string;
};

const REPORT_FORMATS: ReportFormat[] = ["html", "markdown", "json"];

let lastRunSync = 0;
let lastArchiveSync = 0;
let riskySamplePromise: Promise<RiskySigninSample> | null = null;

function startGuiRuntimeFixes() {
  applyGuiRuntimeFixes();

  const observer = new MutationObserver(() => applyGuiRuntimeFixes());
  observer.observe(document.body, { childList: true, subtree: true });

  window.setInterval(applyGuiRuntimeFixes, 2500);
}

function applyGuiRuntimeFixes() {
  wireHelpAndDocsButton();
  enableLoadedModuleReportButtons();
  void syncOverviewRuns();
  void syncArchiveSummary();
  void installRiskySigninReportCard();
}

function wireHelpAndDocsButton() {
  const button = document.querySelector<HTMLButtonElement>(".help-link");

  if (!button || button.dataset.guiFixWired === "true") {
    return;
  }

  button.dataset.guiFixWired = "true";
  button.title = "Open report and demo guidance";
  button.setAttribute("aria-label", "Open report and demo guidance");
  button.addEventListener("click", () => {
    window.location.hash = "reports";
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  });
}

function enableLoadedModuleReportButtons() {
  const hasFindings = document.querySelectorAll(".finding-table .table-row").length > 0;

  if (!hasFindings) {
    return;
  }

  document.querySelectorAll<HTMLButtonElement>(".workspace-hero .report-buttons button:disabled").forEach((button) => {
    button.disabled = false;
    button.removeAttribute("disabled");
    button.title = "Generate report from loaded findings";
  });
}

async function syncOverviewRuns() {
  const overview = document.querySelector(".professional-dashboard-shell");

  if (!overview || Date.now() - lastRunSync < 3000) {
    return;
  }

  lastRunSync = Date.now();

  try {
    const response = await apiFetch("/api/runs?limit=100");

    if (!response.ok) {
      return;
    }

    const data = await response.json();
    const runs = Array.isArray(data.runs) ? data.runs as EvidenceRun[] : [];
    patchOverviewRunKpis(runs);
    patchOverviewRecentRuns(runs);
  } catch {
    // Overview sync is a UI polish layer; the main app remains authoritative.
  }
}

function patchOverviewRunKpis(runs: EvidenceRun[]) {
  const completed = runs.filter((run) => run.status === "success").length;
  const warnings = runs.filter((run) => run.status === "warning").length;
  const failed = runs.filter((run) => run.status === "failed").length;
  const runStatusNote = runs.length > 0 ? `${completed} completed / ${warnings} warning / ${failed} failed` : "No recorded runs yet";

  setKpiValue("Evidence Runs", String(runs.length), runStatusNote);
  setKpiValue("Completed", String(completed), `${runs.length > 0 ? Math.round((completed / runs.length) * 100) : 0}% success rate`);
  setKpiValue("Warnings", String(warnings), `${runs.length > 0 ? Math.round((warnings / runs.length) * 100) : 0}% of runs`);
  setKpiValue("Failed", String(failed), `${runs.length > 0 ? Math.round((failed / runs.length) * 100) : 0}% of runs`);
}

function setKpiValue(label: string, value: string, note: string) {
  const card = Array.from(document.querySelectorAll<HTMLElement>(".visual-kpi-card")).find((candidate) =>
    candidate.querySelector("span")?.textContent?.trim() === label
  );

  card?.querySelector("strong")?.replaceChildren(document.createTextNode(value));
  card?.querySelector("p")?.replaceChildren(document.createTextNode(note));
}

function patchOverviewRecentRuns(runs: EvidenceRun[]) {
  const table = document.querySelector<HTMLElement>(".dashboard-run-table");

  if (!table || runs.length === 0 || table.dataset.guiFixRunSync === String(runs.length)) {
    return;
  }

  table.dataset.guiFixRunSync = String(runs.length);
  const existingEmpty = table.querySelector(".dashboard-empty-run-state");
  existingEmpty?.remove();

  const head = table.querySelector(".dashboard-run-head");
  table.querySelectorAll(".dashboard-run-row.runtime-run-row").forEach((row) => row.remove());

  for (const run of runs.slice(0, 5)) {
    const row = document.createElement("div");
    row.className = "dashboard-run-row runtime-run-row";
    row.innerHTML = `
      <div><strong></strong><span></span></div>
      <span></span>
      <span class="status-pill ${escapeAttribute(run.status)}"></span>
      <strong></strong>
    `;
    row.querySelector("strong")!.textContent = run.module_name;
    row.querySelector("div span")!.textContent = run.asset || run.source;
    row.children[1].textContent = run.source_type;
    row.children[2].textContent = run.status;
    row.children[3].textContent = String(run.finding_count);
    head?.insertAdjacentElement("afterend", row);
  }
}

async function syncArchiveSummary() {
  const archive = document.querySelector(".archive-table");

  if (!archive || Date.now() - lastArchiveSync < 3000) {
    return;
  }

  lastArchiveSync = Date.now();

  try {
    const response = await apiFetch("/api/reports/archive");

    if (!response.ok) {
      return;
    }

    const data = await response.json();
    const entries = Array.isArray(data.reports) ? data.reports as ArchiveEntry[] : [];
    const latest = entries.sort((a, b) => getArchiveTime(b.created_at) - getArchiveTime(a.created_at) || a.filename.localeCompare(b.filename))[0];

    if (!latest) {
      return;
    }

    const latestMetric = Array.from(document.querySelectorAll<HTMLElement>(".report-archive-metric")).find((card) =>
      card.querySelector("span")?.textContent?.trim() === "Latest Report"
    );

    if (!latestMetric) {
      return;
    }

    latestMetric.querySelector("strong")?.replaceChildren(document.createTextNode(getArchiveDisplayLabel(latest)));
    latestMetric.querySelector("p")?.replaceChildren(document.createTextNode(latest.filename));
  } catch {
    // Archive sync is visual polish only.
  }
}

async function installRiskySigninReportCard() {
  const grid = document.querySelector<HTMLElement>(".report-readiness-grid");

  if (!grid || document.querySelector(".risky-signin-report-card")) {
    return;
  }

  const sample = await getRiskySigninSample();
  const ready = sample.findings.length > 0;
  const card = document.createElement("section");
  card.className = `card report-readiness-card risky-signin-report-card ${ready ? "ready" : "blocked"}`;
  card.innerHTML = `
    <div class="card-header">
      <div>
        <p class="eyebrow">SOC Scenario</p>
        <h2>Risky Sign-In Report</h2>
      </div>
      <span class="${ready ? "pill success" : "pill muted"}">${ready ? "Ready" : "No evidence"}</span>
    </div>
    <p>Synthetic Entra-style risky sign-in triage evidence, safe escalation wording, limitations, and non-actions.</p>
    <div class="report-buttons"></div>
    <p class="runtime-sync-note">Backend/API scenario surfaced in the GUI report center.</p>
  `;

  const buttonContainer = card.querySelector(".report-buttons")!;
  for (const format of REPORT_FORMATS) {
    const button = document.createElement("button");
    button.type = "button";
    button.disabled = !ready;
    button.textContent = format === "html" ? "HTML" : format === "markdown" ? "Markdown" : "JSON";
    button.addEventListener("click", () => void downloadRiskySigninReport(format));
    buttonContainer.appendChild(button);
  }

  grid.insertBefore(card, grid.lastElementChild);
}

async function getRiskySigninSample(): Promise<RiskySigninSample> {
  if (!riskySamplePromise) {
    riskySamplePromise = apiFetch("/api/risky-signins/sample-findings")
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(await response.text());
        }

        const data = await response.json();
        return {
          evidence: data.evidence ?? null,
          findings: Array.isArray(data.findings) ? data.findings as Finding[] : []
        };
      })
      .catch(() => ({ evidence: null, findings: [] }));
  }

  return riskySamplePromise;
}

async function downloadRiskySigninReport(format: ReportFormat) {
  const sample = await getRiskySigninSample();

  if (!sample.evidence && sample.findings.length === 0) {
    return;
  }

  const response = await apiFetch("/api/reports/risky-signins", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      evidence: sample.evidence ?? {
        source_type: "risky_signin_session_evidence",
        source_file: "sample-risky-signins.json",
        finding_count: sample.findings.length
      },
      findings: sample.findings,
      format,
      archive: true
    })
  });

  if (!response.ok) {
    return;
  }

  const data = await response.json();
  downloadTextFile(String(data.filename), String(data.content), String(data.content_type));
  lastArchiveSync = 0;
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

function getArchiveDisplayLabel(entry: ArchiveEntry) {
  if (entry.created_at) {
    const parsed = new Date(entry.created_at);

    if (!Number.isNaN(parsed.getTime())) {
      return parsed.toLocaleDateString();
    }
  }

  return entry.format ? entry.format.toUpperCase() : "Available";
}

function getArchiveTime(value?: string) {
  if (!value) {
    return 0;
  }

  const parsed = new Date(value).getTime();
  return Number.isNaN(parsed) ? 0 : parsed;
}

function escapeAttribute(value: string) {
  return value.replace(/[^a-zA-Z0-9_-]/g, "");
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", startGuiRuntimeFixes, { once: true });
} else {
  startGuiRuntimeFixes();
}
