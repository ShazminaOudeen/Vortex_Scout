import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import type { Anomaly } from "@/lib/types";

export function AnomalyTable({ rows }: { rows: Anomaly[] }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-scout-border bg-scout-surface">
      <div className="border-b border-scout-border p-4">
        <h3 className="text-base font-semibold text-zinc-900">
          Detected Shelf-Void Anomalies
        </h3>
        <p className="text-xs text-scout-muted">
          Active and historical inventory discrepancies flagged by Scout.
        </p>
      </div>
      <table className="w-full text-left text-sm">
        <thead className="bg-zinc-50 text-xs uppercase text-scout-muted">
          <tr>
            <th className="p-3">Product</th>
            <th className="p-3">Category</th>
            <th className="p-3">Aisle/Bay</th>
            <th className="p-3">Ledger</th>
            <th className="p-3">P(void)</th>
            <th className="p-3">Status</th>
            <th className="p-3 text-right">Details</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={7} className="p-6 text-center text-sm text-scout-muted">
                No anomalies recorded.
              </td>
            </tr>
          ) : (
            rows.map((r) => (
              <tr key={r.id} className="border-t border-scout-border hover:bg-zinc-50/50">
                <td className="p-3 font-medium text-zinc-900">{r.sku_name}</td>
                <td className="p-3 text-zinc-600">{r.category}</td>
                <td className="p-3 text-zinc-600">
                  {r.aisle} / {r.bay}
                </td>
                <td className="p-3 font-mono">{r.ledger_stock}</td>
                <td className="p-3 font-mono font-medium text-violet-700">
                  {(r.p_void * 100).toFixed(0)}%
                </td>
                <td className="p-3">
                  <Badge tone={r.status === "open" ? "alert" : "success"}>
                    {r.status}
                  </Badge>
                </td>
                <td className="p-3 text-right">
                  <Link
                    href={`/inventory/${r.sku_id}`}
                    className="inline-flex items-center text-xs font-medium text-violet-600 hover:text-violet-800"
                  >
                    View SKU →
                  </Link>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
