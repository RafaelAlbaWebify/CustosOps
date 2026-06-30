import { useEffect, useState } from "react";

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
};

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [modules, setModules] = useState<ModuleInfo[]>([]);
  const [foundationFindings, setFoundationFindings] = useState<Finding[]>([]);
  const [endpointFindings, setEndpointFindings] = useState<Finding[]>([]);
  const [error, setError] = useState<string>("");

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

  return (
    <main className="app-shell">
      <section className="hero">
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

      {error && <section className="alert">Backend connection error: {error}</section>}

      <section className="grid">
        <article className="panel">
          <h2>Modules</h2>
          <div className="module-list">
            {modules.map((module) => (
              <div className="module-card" key={module.id}>
                <div>
                  <h3>{module.name}</h3>
                  <p>{module.description}</p>
                </div>
                <span>{module.status}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <h2>Foundation Status</h2>
          {foundationFindings.map((finding) => (
            <FindingCard finding={finding} key={finding.finding_id} compact />
          ))}
        </article>
      </section>

      <section className="panel wide-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Endpoint Security Evidence v0.1</p>
            <h2>Sample endpoint findings</h2>
          </div>
          <span className="count-pill">{endpointFindings.length} findings</span>
        </div>

        <div className="findings-grid">
          {endpointFindings.map((finding) => (
            <FindingCard finding={finding} key={finding.finding_id} />
          ))}
        </div>
      </section>
    </main>
  );
}

function FindingCard({ finding, compact = false }: { finding: Finding; compact?: boolean }) {
  return (
    <div className="finding-card">
      <div className="finding-topline">
        <p className="eyebrow">{finding.category}</p>
        <span className={`severity severity-${finding.severity}`}>{finding.severity}</span>
      </div>

      <h3>{finding.title}</h3>
      <p>{finding.why_it_matters}</p>

      <dl>
        <div>
          <dt>Confidence</dt>
          <dd>{finding.confidence}</dd>
        </div>
        <div>
          <dt>Affected asset</dt>
          <dd>{finding.affected_asset}</dd>
        </div>
        <div>
          <dt>Finding ID</dt>
          <dd>{finding.finding_id}</dd>
        </div>
      </dl>

      {!compact && (
        <>
          <h4>Safe next steps</h4>
          <ul>
            {finding.safe_next_steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ul>

          <h4>Limitations</h4>
          <ul>
            {finding.limitations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}