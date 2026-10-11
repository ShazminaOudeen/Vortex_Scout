import type {
  Anomaly,
  AuditFeedItem,
  AuditStats,
  Checklist,
  DashboardMetrics,
  DetectionRunResult,
  EvaluationReport,
  PosTransactionFeedItem,
  ReconcilePayload,
  ReconcileResult,
  SkuDetail,
  SkuWithStatus,
  UndoPayload,
  UndoResult,
  VelocityResponse,
} from "./types";

const RAW_API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const API_URL = RAW_API_URL.replace(/\/+$/, "");

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
  // /pos
  getRecentTransactions: (limit = 50, skuId?: string) =>
    request<PosTransactionFeedItem[]>(
      `/api/v1/pos/recent?limit=${limit}${skuId ? `&sku_id=${skuId}` : ""}`
    ),
  // /simulate hub
  injectScenario: (scenario: "phantom" | "normal" | "reset") =>
    request<{ ok: boolean; scenario: string } & Record<string, unknown>>(
      `/api/v1/simulate/${scenario}`,
      { method: "POST" },
    ),
  runDetection: () =>
    request<DetectionRunResult>("/api/v1/anomalies/run", { method: "POST" }),
  // /evaluation (Feature F3, F4)
  getEvaluation: (fresh = false) =>
    request<EvaluationReport>(`/api/v1/evaluation${fresh ? "?fresh=true" : ""}`),
  runEvaluation: (quick = false, threshold = 0.75) =>
    request<EvaluationReport>(
      `/api/v1/evaluation/run?quick=${quick}&threshold=${threshold}`,
      { method: "POST" }
    ),
};


