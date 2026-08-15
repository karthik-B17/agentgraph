import { useEffect, useState } from "react";
import { getFailureClusters } from "../api/client";
import LoadingState from "../components/LoadingState";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";

export default function FailurePatterns() {
  const [clusters, setClusters] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getFailureClusters().then(setClusters).catch(setError);
  }, []);

  return (
    <>
      <h1 className="page-title">Failure Patterns</h1>
      <p className="page-subtitle">
        Tasks across different runs that failed for the exact same underlying reason —
        the kind of pattern a relational join would struggle to surface cleanly.
      </p>

      {error && <ErrorState error={error} />}
      {!error && !clusters && <LoadingState label="Scanning for shared failures" />}
      {!error && clusters && clusters.length === 0 && (
        <EmptyState
          label="No shared failure patterns found"
          detail="This means every failure in the graph currently has a distinct cause."
        />
      )}

      {!error && clusters && clusters.length > 0 && (
        <div className="card">
          {clusters.map((cluster) => (
            <div key={cluster.output_id} className="cluster-card">
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <span className="status-pill failed">
                  <span className="dot" />
                  {cluster.affected_task_ids.length} tasks
                </span>
                <span style={{ fontWeight: 500 }}>{cluster.shared_error}</span>
              </div>
              <div className="text-muted mono" style={{ fontSize: 12 }}>
                {cluster.affected_task_ids.map((id) => id.slice(0, 8)).join("  ·  ")}
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
