"use client";
import useSWR from "swr";
import { api } from "@/lib/api";
import { mockAnomalies, mockChecklist, mockMetrics } from "@/lib/mock";

// Each hook falls back to mock data if the backend isn't running.
// Remove the fallback once the real endpoints are live.
export function useAnomalies() {
  return useSWR("anomalies", () => api.getAnomalies().catch(() => mockAnomalies), {
    refreshInterval: 10_000,
  });
}

export function useChecklist() {
  return useSWR("checklist", () => api.getChecklist().catch(() => mockChecklist));
}

export function useMetrics() {
  return useSWR("metrics", () => api.getMetrics().catch(() => mockMetrics), {
    refreshInterval: 10_000,
  });
}

export function useVelocity(options?: { anomalyId?: string; skuId?: string }) {
  const key = options?.anomalyId
    ? `velocity-anomaly-${options.anomalyId}`
    : options?.skuId
    ? `velocity-sku-${options.skuId}`
    : null;

  return useSWR(
    key,
    async () => {
      if (options?.anomalyId) {
        return api.getAnomalyVelocity(options.anomalyId);
      }
      if (options?.skuId) {
        return api.getSkuVelocity(options.skuId);
      }
      return null;
    },
    { refreshInterval: 15_000 }
  );
}

export function useAuditFeed(limit = 20, skuId?: string) {
  return useSWR(
    ["audit-feed", limit, skuId],
    () => api.getAuditFeed(limit, skuId).catch(() => []),
    { refreshInterval: 10_000 }
  );
}

export function useSkus() {
  return useSWR("skus", () => api.getSkus().catch(() => []), {
    refreshInterval: 15_000,
  });
}

export function useSku(id?: string) {
  return useSWR(id ? `sku-${id}` : null, () => (id ? api.getSku(id) : null));
}

