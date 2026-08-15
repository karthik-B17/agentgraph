import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const client = axios.create({ baseURL: BASE_URL, timeout: 10000 });

export async function listRuns() {
  const res = await client.get("/runs");
  return res.data;
}

export async function getRun(runId) {
  const res = await client.get(`/runs/${runId}`);
  return res.data;
}

export async function getDelegationChain(agentId) {
  const res = await client.get(`/agents/${agentId}/delegation-chain`);
  return res.data;
}

export async function traceFailure(taskId) {
  const res = await client.get(`/analytics/tasks/${taskId}/failure-trace`);
  return res.data;
}

export async function getFailureClusters() {
  const res = await client.get("/analytics/failure-clusters");
  return res.data;
}
