import type {
  Anomaly,
  AuditFeedItem,
  AuditStats,
  Checklist,
  DashboardMetrics,
  ReconcilePayload,
  ReconcileResult,
  SkuDetail,
  SkuWithStatus,
  UndoPayload,
  UndoResult,
  VelocityResponse,
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
  getAnomalyVelocity: (id: string) =>
    request<VelocityResponse>(`/api/v1/anomalies/${id}/velocity`),
  getChecklist: () => request<Checklist>("/api/v1/agent/checklist"),
  getMetrics: () => request<DashboardMetrics>("/api/v1/anomalies/metrics"),
  reconcile: (body: ReconcilePayload) =>
    request<ReconcileResult>("/api/v1/audit/reconcile", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  undoReconcile: (body: UndoPayload) =>
    request<UndoResult>("/api/v1/audit/undo", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getAuditStats: () => request<AuditStats>("/api/v1/audit/stats"),
  getAuditFeed: (limit = 50, skuId?: string) =>
    request<AuditFeedItem[]>(
      `/api/v1/audit/feed?limit=${limit}${skuId ? `&sku_id=${skuId}` : ""}`
    ),
  getSkus: () => request<SkuWithStatus[]>("/api/v1/skus"),
  getSku: (id: string) => request<SkuDetail>(`/api/v1/skus/${id}`),
  getSkuVelocity: (id: string) =>
    request<VelocityResponse>(`/api/v1/skus/${id}/velocity`),
  // /simulate hub
  injectScenario: (scenario: "phantom" | "normal" | "reset") =>
    request<{ ok: boolean; scenario: string } & Record<string, unknown>>(
      `/api/v1/simulate/${scenario}`,
      { method: "POST" },
    ),
  runDetection: () =>
    request<{ flagged: number }>("/api/v1/anomalies/run", { method: "POST" }),
};

