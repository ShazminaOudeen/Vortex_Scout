import { formatLKR } from "@/lib/utils";
import type { DashboardMetrics } from "@/lib/types";

export function MetricCards({ m }: { m: DashboardMetrics }) {
  const cards = [
    { label: "Revenue recovered (month)", value: formatLKR(m.revenue_recovered_lkr) },
    { label: "Active phantom voids", value: `${m.active_voids} SKUs` },
    { label: "Audit completion rate", value: `${Math.round(m.audit_completion_rate * 100)}%` },
    { label: "Inventory record inaccuracy", value: `${(m.iri_rate * 100).toFixed(1)}%` },
  ];
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {cards.map((c) => (
        <div key={c.label} className="rounded-xl border border-scout-border bg-scout-surface p-4">
          <p className="text-xs text-scout-muted">{c.label}</p>
          <p className="mt-1 text-2xl font-bold">{c.value}</p>
        </div>
      ))}
    </div>
  );
}
