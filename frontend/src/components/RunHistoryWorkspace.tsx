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

export function RunHistoryWorkspace(props: {
  runs: EvidenceRun[];
  onRefresh: () => void;
  onClear: () => void;
}) {
  const totalFindings = props.runs.reduce((sum, run) => sum + run.finding_count, 0);
  const warningRuns = props.runs.filter((run) => run.status === "warning").length;
  const failedRuns = props.runs.filter((run) => run.status === "failed").length;

  return (
    <section className="workspace">
      <div className="workspace-header">
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

      <div className="metric-grid">
        <div className="metric-card">
          <span>Runs</span>
          <strong>{props.runs.length}</strong>
        </div>
        <div className="metric-card">
          <span>Total findings</span>
          <strong>{totalFindings}</strong>
        </div>
        <div className="metric-card">
          <span>Warnings</span>
          <strong>{warningRuns}</strong>
        </div>
        <div className="metric-card">
          <span>Failed</span>
          <strong>{failedRuns}</strong>
        </div>
      </div>

      <div className="panel">
        {props.runs.length === 0 ? (
          <p className="muted">No evidence runs recorded yet. Automatic workflow recording will be added in the next slice.</p>
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
                {props.runs.map((run) => (
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

function formatRunDate(value: string) {
  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString();
}
