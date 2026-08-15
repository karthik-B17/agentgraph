import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listRuns } from "../api/client";
import LoadingState from "../components/LoadingState";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import StatusPill from "../components/StatusPill";

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function Dashboard() {
  const [runs, setRuns] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    listRuns()
      .then(setRuns)
      .catch(setError);
  }, []);

  const failedCount = runs?.filter((r) => r.status === "failed").length ?? 0;

  return (
    <>
      <h1 className="page-title">Runs</h1>
      <p className="page-subtitle">
        {runs
          ? `${runs.length} runs · ${failedCount} failed`
          : "Every agent execution, most recent first."}
      </p>

      {error && <ErrorState error={error} />}
      {!error && !runs && <LoadingState label="Loading runs" />}
      {!error && runs && runs.length === 0 && (
        <EmptyState label="No runs yet" detail="Seed the database to see runs here." />
      )}

      {!error && runs && runs.length > 0 && (
        <div className="card">
          <div className="run-row run-row-header">
            <div>Agent</div>
            <div>Status</div>
            <div>Trigger</div>
            <div>Started</div>
          </div>
          {runs.map((run) => (
            <Link key={run.id} to={`/runs/${run.id}`} className="run-row">
              <div>{run.primary_agent}</div>
              <div>
                <StatusPill status={run.status} />
              </div>
              <div className="text-muted mono">{run.trigger}</div>
              <div className="text-muted mono">{formatDate(run.started_at)}</div>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
