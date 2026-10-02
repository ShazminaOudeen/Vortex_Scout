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
