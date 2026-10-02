import { Badge } from "@/components/ui/Badge";
import type { Anomaly } from "@/lib/types";

export function AnomalyTable({ rows }: { rows: Anomaly[] }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-scout-border bg-scout-surface">
      <table className="w-full text-left text-sm">
        <thead className="bg-zinc-50 text-xs uppercase text-scout-muted">
          <tr>
            <th className="p-3">Product</th><th className="p-3">Category</th><th className="p-3">Aisle/Bay</th>
            <th className="p-3">Ledger</th><th className="p-3">P(void)</th><th className="p-3">Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id} className="border-t border-scout-border">
              <td className="p-3 font-medium">{r.sku_name}</td>
              <td className="p-3">{r.category}</td>
              <td className="p-3">{r.aisle} / {r.bay}</td>
              <td className="p-3">{r.ledger_stock}</td>
              <td className="p-3">{r.p_void.toFixed(2)}</td>
              <td className="p-3">
                <Badge tone={r.status === "open" ? "alert" : "success"}>{r.status}</Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
