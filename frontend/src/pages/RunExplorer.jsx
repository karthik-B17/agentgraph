import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getRun, traceFailure } from "../api/client";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";
import StatusPill from "../components/StatusPill";

export default function RunExplorer() {
  const { runId } = useParams();
  const [run, setRun] = useState(null);
  const [error, setError] = useState(null);
  const [traceResult, setTraceResult] = useState(null);
  const [tracingTaskId, setTracingTaskId] = useState(null);
  const [traceError, setTraceError] = useState(null);

  useEffect(() => {
    setRun(null);
    setTraceResult(null);
    getRun(runId).then(setRun).catch(setError);
  }, [runId]);

  async function handleTrace(taskId) {
    setTracingTaskId(taskId);
    setTraceError(null);
    setTraceResult(null);
    try {
      const result = await traceFailure(taskId);
      setTraceResult(result);
    } catch (e) {
      setTraceError(e);
    }
  }

  if (error) return <ErrorState error={error} />;
  if (!run) return <LoadingState label="Loading run" />;

  const tasks = run.tasks || [];

  return (
    <>
      <Link to="/" className="text-muted mono" style={{ fontSize: 12, textDecoration: "none" }}>
        ← Back to runs
      </Link>
      <h1 className="page-title" style={{ marginTop: 12 }}>
        {run.primary_agent}
      </h1>
      <p className="page-subtitle">
        Run <span className="mono">{run.run_id.slice(0, 8)}</span> ·{" "}
        <StatusPill status={run.run_status} />
      </p>

      {tasks.length === 0 && <EmptyState label="No tasks recorded for this run" />}

      {tasks.length > 0 && (
        <div className="trace">
          {tasks.map((task) => {
            const failed = task.status === "failed";
            const isRootCause =
              traceResult && traceResult.root_cause_task_id === task.task_id;
            const nodeClass = isRootCause ? "root-cause" : failed ? "failed" : "success";

            return (
              <div key={task.task_id} className={`trace-node ${nodeClass}`}>
                <div className={`trace-card ${isRootCause ? "root-cause" : ""}`}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div>
                      <div style={{ fontWeight: 500, marginBottom: 4 }}>{task.description}</div>
                      <div className="text-muted mono" style={{ fontSize: 12 }}>
                        {task.agent} → called <strong>{task.tool}</strong>
                      </div>
                    </div>
                    <StatusPill status={task.status} />
                  </div>

                  <div className="text-muted" style={{ fontSize: 13, marginTop: 8 }}>
                    {task.output_summary}
                  </div>

                  {failed && (
                    <div style={{ marginTop: 12 }}>
                      <button
                        className="btn btn-danger"
                        onClick={() => handleTrace(task.task_id)}
                      >
                        Trace root cause
                      </button>
                    </div>
                  )}

                  {tracingTaskId === task.task_id && traceError && (
                    <div style={{ color: "var(--failure)", fontSize: 12, marginTop: 8 }}>
                      Couldn't trace this failure — the database may be unreachable.
                    </div>
                  )}

                  {tracingTaskId === task.task_id && traceResult && (
                    <div
                      style={{
                        marginTop: 12,
                        padding: 10,
                        borderRadius: 6,
                        background: "var(--root-cause-dim)",
                        border: "1px solid var(--root-cause)",
                        fontSize: 13,
                      }}
                    >
                      <div className="mono" style={{ fontSize: 11, color: "var(--root-cause)", marginBottom: 4 }}>
                        ROOT CAUSE
                      </div>
                      {traceResult.root_cause_task_id ? (
                        <>
                          <div>{traceResult.root_cause_description}</div>
                          <div className="text-muted" style={{ marginTop: 4 }}>
                            {traceResult.error_message}
                          </div>
                        </>
                      ) : (
                        <div className="text-muted">No upstream failure found — this task failed on its own.</div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </>
  );
}
