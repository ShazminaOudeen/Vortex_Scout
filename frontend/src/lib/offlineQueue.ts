// Offline queue management and connectivity synchronization (Feature D3)
import { api } from "./api";
import type { ReconcilePayload } from "./types";

const QUEUE_STORAGE_KEY = "scout_offline_reconcile_queue";

export function getOfflineQueue(): ReconcilePayload[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(QUEUE_STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function queueOfflineReconcile(payload: ReconcilePayload): void {
  if (typeof window === "undefined") return;
  const current = getOfflineQueue();
  // Avoid duplicates
  const filtered = current.filter((item) => item.anomaly_id !== payload.anomaly_id);
  filtered.push(payload);
  localStorage.setItem(QUEUE_STORAGE_KEY, JSON.stringify(filtered));
}

export function clearOfflineQueue(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(QUEUE_STORAGE_KEY);
}

export async function flushOfflineQueue(): Promise<number> {
  if (typeof window === "undefined" || !navigator.onLine) return 0;
  const queue = getOfflineQueue();
  if (queue.length === 0) return 0;

  let flushedCount = 0;
  const remaining: ReconcilePayload[] = [];

  for (const item of queue) {
    try {
      await api.reconcile(item);
      flushedCount++;
    } catch {
      remaining.push(item);
    }
  }

  if (remaining.length === 0) {
    clearOfflineQueue();
  } else {
    localStorage.setItem(QUEUE_STORAGE_KEY, JSON.stringify(remaining));
  }

  return flushedCount;
}
