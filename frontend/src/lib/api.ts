import type {
  Anomaly,
  AuditStats,
  Checklist,
  DashboardMetrics,
  ReconcilePayload,
  ReconcileResult,
} from "./types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${path}`);
  return res.json() as Promise<T>;
}

export const api = {
  getAnomalies: () => request<Anomaly[]>("/api/v1/anomalies"),
  getChecklist: () => request<Checklist>("/api/v1/agent/checklist"),
  getMetrics: () => request<DashboardMetrics>("/api/v1/anomalies/metrics"),
  reconcile: (body: ReconcilePayload) =>
    request<ReconcileResult>("/api/v1/audit/reconcile", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getAuditStats: () => request<AuditStats>("/api/v1/audit/stats"),
  // /simulate hub
  injectScenario: (scenario: "phantom" | "normal" | "reset") =>
    request<{ ok: boolean; scenario: string } & Record<string, unknown>>(
      `/api/v1/simulate/${scenario}`,
      { method: "POST" },
    ),
  runDetection: () =>
    request<{ flagged: number }>("/api/v1/anomalies/run", { method: "POST" }),
};
