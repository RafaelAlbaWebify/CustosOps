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

type RunStatus = EvidenceRun["status"];

type ModuleRunSummary = {
  moduleId: string;
  moduleName: string;
  runCount: number;
  findingCount: number;
  highCount: number;
  warningCount: number;
  failedCount: number;
  latestAt: string;
  worstStatus: RunStatus;
};

export function RunHistoryWorkspace(props: {
  runs: EvidenceRun[];
  onRefresh: () => void;
  onClear: () => void;
}) {
  const sortedRuns = [...props.runs].sort((a, b) => getRunTime(b.created_at) - getRunTime(a.created_at));
  const totalFindings = props.runs.reduce((sum, run) => sum + run.finding_count, 0);
  const totalRaw = props.runs.reduce((sum, run) => sum + run.raw_count, 0);
  const totalParsed = props.runs.reduce((sum, run) => sum + run.parsed_count, 0);
  const reportsLinked = props.runs.reduce((sum, run) => sum + run.report_ids.length, 0);
  const successRuns = props.runs.filter((run) => run.status === "success").length;
  const warningRuns = props.runs.filter((run) => run.status === "warning").length;
  const failedRuns = props.runs.filter((run) => run.status === "failed").length;
  const moduleSummaries = getModuleRunSummaries(props.runs);
  const latestRun = sortedRuns[0] ?? null;
  const lastRunLabel = latestRun ? formatRunDate(latestRun.created_at) : "No runs yet";
  const outcomeStats = [
    { status: "success" as RunStatus, label: "Completed", count: successRuns },
    { status: "warning" as RunStatus, label: "Warning", count: warningRuns },
    { status: "failed" as RunStatus, label: "Failed", count: failedRuns }
  ];

  return (
    <section className="workspace run-history-workspace">
      <div className="workspace-header run-history-header">
        <div>
          <p className="eyebrow">Evidence run history</p>
          <h2>Run History</h2>
          <p className="muted">
            Local timeline of evidence runs recorded by CustosOps. This is local-only operational metadata.
          </p>
        </div>
        <div className="actions">
          <button type="button" className="button secondary" onClick={props.onRefresh}>
            Refresh
          </button>
          <button type="button" className="button danger" onClick={props.onClear} disabled={props.runs.length === 0}>
            Clear History
          </button>
        </div>
      </div>

      <section className="run-history-hero">
        <div>
          <p className="eyebrow">Local operations timeline</p>
          <h3>{props.runs.length > 0 ? `${props.runs.length} evidence runs recorded` : "No evidence runs recorded yet"}</h3>
          <p>
            Track evidence collection/import activity, finding counts, report links, and run outcomes without sending operational metadata outside the workstation.
          </p>
        </div>
        <div className="run-history-hero-panel">
          <span>Latest run</span>
          <strong>{latestRun ? latestRun.module_name : "Awaiting evidence"}</strong>
          <p>{lastRunLabel}</p>
        </div>
      </section>

      <div className="metric-grid run-history-kpi-grid">
        <RunHistoryMetricCard label="Runs" value={props.runs.length} note="Local history entries" tone="primary" />
        <RunHistoryMetricCard label="Total Findings" value={totalFindings} note="Across all recorded runs" tone="warning" />
        <RunHistoryMetricCard label="Parsed Evidence" value={totalParsed} note={`Raw records: ${totalRaw}`} tone="teal" />
        <RunHistoryMetricCard label="Reports Linked" value={reportsLinked} note="Report IDs referenced" tone="purple" />
      </div>

      <section className="run-history-analytics-grid">
        <section className="card run-outcome-card">
          <div className="card-header">
            <div>
              <p className="eyebrow">Run outcomes</p>
              <h2>Outcome Distribution</h2>
            </div>
            <span className="pill">{props.runs.length} total</span>
          </div>

          <div className="run-outcome-bar" aria-label="Run outcome distribution">
            {outcomeStats.map((outcome) => (
              <span
                className={`run-outcome-segment ${outcome.status}`}
                key={outcome.status}
                style={{ width: `${getRunPercentage(outcome.count, props.runs.length)}%` }}
                title={`${outcome.label}: ${outcome.count}`}
              />
            ))}
          </div>

          <div className="run-outcome-legend">
            {outcomeStats.map((outcome) => (
              <div key={outcome.status}>
                <span className={`run-status-dot ${outcome.status}`} />
                <strong>{outcome.count}</strong>
                <em>{outcome.label}</em>
              </div>
            ))}
          </div>
        </section>

        <section className="card module-run-card">
          <div className="card-header">
            <div>
              <p className="eyebrow">Modules</p>
              <h2>Runs by Evidence Source</h2>
            </div>
            <span className="pill">{moduleSummaries.length} modules</span>
          </div>

          <div className="module-run-list">
            {moduleSummaries.slice(0, 5).map((module) => (
              <div className="module-run-row" key={module.moduleId}>
                <div className="module-run-main">
                  <span className={`run-status-dot ${module.worstStatus}`} />
                  <div>
                    <strong>{module.moduleName}</strong>
                    <span>{module.runCount} runs - {module.findingCount} findings</span>
                  </div>
                </div>
                <div className="module-run-counts">
                  <span>High {module.highCount}</span>
                  <span>Warn {module.warningCount}</span>
                  <span>Fail {module.failedCount}</span>
                </div>
              </div>
            ))}

            {moduleSummaries.length === 0 && <p className="muted">No module activity recorded yet.</p>}
          </div>
        </section>

        <section className="card run-timeline-card">
          <div className="card-header">
            <div>
              <p className="eyebrow">Timeline</p>
              <h2>Latest Activity</h2>
            </div>
            <span className="pill">{Math.min(sortedRuns.length, 5)} shown</span>
          </div>

          <div className="run-timeline-list">
            {sortedRuns.slice(0, 5).map((run) => (
              <div className="run-timeline-row" key={run.run_id}>
                <span className={`run-status-dot ${run.status}`} />
                <div>
                  <strong>{run.module_name}</strong>
                  <span>{formatRunDate(run.created_at)} - {run.finding_count} findings - {run.asset || run.source}</span>
                </div>
              </div>
            ))}

            {sortedRuns.length === 0 && <p className="muted">Run activity will appear here after evidence is imported or collected.</p>}
          </div>
        </section>
      </section>

      <div className="panel">
        {props.runs.length === 0 ? (
          <p className="muted">Evidence imports and local collections will appear here after they run.</p>
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Module</th>
                  <th>Source</th>
                  <th>Asset</th>
                  <th>Status</th>
                  <th>Counts</th>
                  <th>Run ID</th>
                </tr>
              </thead>
              <tbody>
                {sortedRuns.map((run) => (
                  <tr key={run.run_id}>
                    <td>{formatRunDate(run.created_at)}</td>
                    <td>
                      <strong>{run.module_name}</strong>
                      <br />
                      <span className="muted">{run.module_id}</span>
                    </td>
                    <td>
                      {run.source}
                      <br />
                      <span className="muted">{run.source_type}</span>
                    </td>
                    <td>{run.asset}</td>
                    <td>
                      <span className={`status-pill ${run.status}`}>{run.status}</span>
                    </td>
                    <td>
                      Raw {run.raw_count} / Parsed {run.parsed_count}
                      <br />
                      Findings {run.finding_count} / High {run.high_count} / Medium {run.medium_count} / Low {run.low_count}
                    </td>
                    <td>
                      <code>{run.run_id}</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

function RunHistoryMetricCard(props: { label: string; value: number; note: string; tone: string }) {
  return (
    <div className={`metric-card run-history-metric tone-${props.tone}`}>
      <span>{props.label}</span>
      <strong>{props.value}</strong>
      <p>{props.note}</p>
    </div>
  );
}

function getModuleRunSummaries(runs: EvidenceRun[]): ModuleRunSummary[] {
  const summaries = new Map<string, ModuleRunSummary>();

  for (const run of runs) {
    const key = run.module_id || run.module_name;
    const existing = summaries.get(key);

    if (!existing) {
      summaries.set(key, {
        moduleId: key,
        moduleName: run.module_name || run.module_id,
        runCount: 1,
        findingCount: run.finding_count,
        highCount: run.high_count,
        warningCount: run.status === "warning" ? 1 : 0,
        failedCount: run.status === "failed" ? 1 : 0,
        latestAt: run.created_at,
        worstStatus: run.status
      });
      continue;
    }

    existing.runCount += 1;
    existing.findingCount += run.finding_count;
    existing.highCount += run.high_count;
    existing.warningCount += run.status === "warning" ? 1 : 0;
    existing.failedCount += run.status === "failed" ? 1 : 0;

    if (getRunTime(run.created_at) > getRunTime(existing.latestAt)) {
      existing.latestAt = run.created_at;
    }

    existing.worstStatus = getWorstRunStatus(existing.worstStatus, run.status);
  }

  return Array.from(summaries.values()).sort((a, b) => b.runCount - a.runCount || b.findingCount - a.findingCount);
}

function getWorstRunStatus(a: RunStatus, b: RunStatus): RunStatus {
  const weight: Record<RunStatus, number> = {
    success: 0,
    warning: 1,
    failed: 2
  };

  return weight[b] > weight[a] ? b : a;
}

function getRunPercentage(count: number, total: number) {
  if (total <= 0 || count <= 0) {
    return 0;
  }

  return Math.max(4, Math.round((count / total) * 100));
}

function getRunTime(value: string) {
  const parsed = new Date(value).getTime();

  return Number.isNaN(parsed) ? 0 : parsed;
}

function formatRunDate(value: string) {
  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString();
}
