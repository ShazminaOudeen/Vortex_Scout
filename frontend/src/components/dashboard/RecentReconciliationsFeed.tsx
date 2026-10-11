"use client";

import { Badge } from "@/components/ui/Badge";
import { useAuditFeed } from "@/hooks/useAnomalies";

interface RecentReconciliationsFeedProps {
  limit?: number;
}

export function RecentReconciliationsFeed({ limit = 10 }: RecentReconciliationsFeedProps) {
  const { data: feed, isLoading } = useAuditFeed(limit);

  return (
    <div className="rounded-xl border border-scout-border bg-scout-surface p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-zinc-900">
            Recent Audit Reconciliations
          </h3>
          <p className="text-xs text-scout-muted">
            Live feed of floor supervisor actions and inventory write-offs.
          </p>
        </div>
        <span className="rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-medium text-zinc-600">
          {feed?.length ?? 0} actions
        </span>
      </div>

      {isLoading ? (
        <div className="flex h-48 items-center justify-center text-sm text-scout-muted">
          Loading audit activity feed...
        </div>
      ) : !feed || feed.length === 0 ? (
        <div className="flex h-48 flex-col items-center justify-center rounded-lg border border-dashed border-zinc-200 p-6 text-center text-sm text-scout-muted">
          <p className="font-medium text-zinc-700">No reconciliation activity yet</p>
          <p className="mt-1 text-xs">
            Actions taken by store staff on the Floor Checklist (/floor) will appear here in real time.
          </p>
        </div>
      ) : (
        <div className="divide-y divide-zinc-100 overflow-y-auto max-h-80 pr-1">
          {feed.map((item) => {
            const timeStr = item.created_at
              ? new Date(item.created_at).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })
              : "";

            return (
              <div key={item.id} className="py-3 first:pt-0 last:pb-0">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-zinc-900 leading-snug">
                      {item.summary}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-scout-muted">
                      <span>{item.category}</span>
                      <span>•</span>
                      <span>
                        Aisle {item.aisle} / Bay {item.bay}
                      </span>
                      {item.associate && (
                        <>
                          <span>•</span>
                          <span>Staff: {item.associate}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1 shrink-0">
                    <Badge
                      tone={
                        item.action === "restocked"
                          ? "success"
                          : item.action === "damaged"
                          ? "alert"
                          : "neutral"
                      }
                    >
                      {item.action === "restocked"
                        ? "Restocked"
                        : item.action === "damaged"
                        ? "Damaged"
                        : "False Alarm"}
                    </Badge>
                    <span className="text-[11px] text-zinc-400">{timeStr}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
