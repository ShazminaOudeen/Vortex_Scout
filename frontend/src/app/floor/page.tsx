"use client";
import { useState } from "react";
import { AisleGroup } from "@/components/floor/AisleGroup";
import { QuickStatsBar } from "@/components/floor/QuickStatsBar";
import { useChecklist } from "@/hooks/useAnomalies";
import { api } from "@/lib/api";
import type { AuditAction } from "@/lib/types";

// TODO(Task 3): completion animation, haptics, optimistic updates.
export default function FloorPage() {
  const { data } = useChecklist();
  const [resolved, setResolved] = useState<Set<string>>(new Set());

  if (!data) return <main className="p-6">Loading checklist…</main>;

  const total = data.groups.reduce((n, g) => n + g.items.length, 0);

  async function handle(id: string, action: AuditAction) {
    setResolved((s) => new Set(s).add(id));
    api.reconcile({ anomaly_id: id, action }).catch(() => {});
  }

  return (
    <main className="mx-auto max-w-[420px] space-y-4 p-4">
      <QuickStatsBar done={resolved.size} total={total} minutes={data.estimated_minutes} />
      <div className="rounded-xl bg-scout-aiBg p-3 text-sm text-scout-ai">{data.briefing}</div>
      {data.groups.map((g) => (
        <AisleGroup
          key={g.aisle}
          group={{ ...g, items: g.items.filter((i) => !resolved.has(i.id)) }}
          onAction={handle}
        />
      ))}
      {resolved.size === total && total > 0 && (
        <p className="text-center text-lg font-semibold text-scout-success">All verified ✓</p>
      )}
    </main>
  );
}
