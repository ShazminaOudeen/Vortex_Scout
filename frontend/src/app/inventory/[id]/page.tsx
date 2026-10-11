"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { VelocityChart } from "@/components/dashboard/VelocityChart";
import { Badge } from "@/components/ui/Badge";
import { useSku } from "@/hooks/useAnomalies";
import { formatLKR } from "@/lib/utils";

export default function SkuDetailPage() {
  const params = useParams();
  const skuId = typeof params?.id === "string" ? params.id : "";
  const { data: detail, isLoading, error } = useSku(skuId);

  if (isLoading) {
    return (
      <main className="mx-auto max-w-6xl space-y-6 p-6">
        <div className="h-6 w-32 animate-pulse rounded bg-zinc-200" />
        <div className="h-40 animate-pulse rounded-xl bg-zinc-100" />
      </main>
    );
  }

  if (error || !detail) {
    return (
      <main className="mx-auto max-w-6xl space-y-4 p-6">
        <Link
          href="/inventory"
          className="text-xs font-medium text-violet-600 hover:text-violet-800"
        >
          ← Back to Inventory Explorer
        </Link>
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-rose-800">
          <h2 className="text-lg font-bold">SKU Not Found</h2>
          <p className="mt-1 text-sm">
            Could not find SKU with ID {skuId}. Please check the catalogue.
          </p>
        </div>
      </main>
    );
  }

  const { sku, open_anomaly, audit_history } = detail;
  const isCritical = sku.has_open_anomaly && sku.p_void >= 0.75;

  return (
    <main className="mx-auto max-w-6xl space-y-6 p-6">
      {/* Navigation */}
      <div className="flex items-center gap-2 text-xs font-medium text-scout-muted">
        <Link href="/inventory" className="hover:text-zinc-900">
          Inventory Explorer
        </Link>
        <span>/</span>
        <span className="text-zinc-800">{sku.name}</span>
      </div>

      {/* Header */}
      <div className="flex flex-col gap-3 rounded-xl border border-scout-border bg-scout-surface p-6 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-zinc-900">{sku.name}</h1>
            {isCritical ? (
              <Badge tone="alert">Critical Void</Badge>
            ) : sku.anomaly_status && sku.anomaly_status !== "open" ? (
              <Badge tone="success">Reconciled</Badge>
            ) : (
              <Badge tone="neutral">Healthy</Badge>
            )}
          </div>
          <p className="mt-1 font-mono text-xs text-scout-muted">
            SKU ID: {sku.id} • Barcode: {sku.barcode} • Category: {sku.category}
          </p>
        </div>
        <Link
          href="/inventory"
          className="inline-flex items-center rounded-lg border border-zinc-200 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 shadow-sm hover:bg-zinc-50"
        >
          ← Return to catalogue
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="rounded-xl border border-scout-border bg-scout-surface p-4">
          <p className="text-xs text-scout-muted">Ledger Stock</p>
          <p className="mt-1 text-2xl font-bold text-zinc-900">
            {sku.ledger_stock} <span className="text-sm font-normal text-zinc-500">units</span>
          </p>
        </div>
        <div className="rounded-xl border border-scout-border bg-scout-surface p-4">
          <p className="text-xs text-scout-muted">Unit Price / Cost</p>
          <p className="mt-1 text-2xl font-bold text-zinc-900">
            {formatLKR(sku.unit_price)}
          </p>
          <p className="text-[11px] text-zinc-400">Cost: {formatLKR(sku.unit_cost)}</p>
        </div>
        <div className="rounded-xl border border-scout-border bg-scout-surface p-4">
          <p className="text-xs text-scout-muted">Store Location</p>
          <p className="mt-1 text-2xl font-bold text-zinc-900">
            Aisle {sku.aisle}
          </p>
          <p className="text-[11px] text-zinc-500">Bay Shelf: {sku.bay}</p>
        </div>
        <div className="rounded-xl border border-scout-border bg-scout-surface p-4">
          <p className="text-xs text-scout-muted">Shelf-Void Probability P(void)</p>
          <p
            className={`mt-1 text-2xl font-bold ${
              isCritical ? "text-rose-600" : "text-violet-700"
            }`}
          >
            {(sku.p_void * 100).toFixed(0)}%
          </p>
          <p className="text-[11px] text-zinc-400">
            Threshold: 75% for automated audit flag
          </p>
        </div>
      </div>

      {/* Active Anomaly Banner */}
      {open_anomaly && (
        <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-5">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
                <h3 className="text-sm font-bold text-amber-900">
                  Active Shelf-Void Anomaly Flagged
                </h3>
              </div>
              <p className="mt-1 text-xs text-amber-800">
                Silence streak: <span className="font-semibold">{open_anomaly.hours_since_last_sale} hrs</span> without sales • 
                Void diagnosis: <span className="font-semibold capitalize">{open_anomaly.void_type || "frozen"}</span> • 
                Suggested floor action: <span className="font-semibold capitalize">{open_anomaly.suggested_action || "restocked"}</span>
              </p>
            </div>
            <Badge tone="alert">Open Anomaly</Badge>
          </div>
        </div>
      )}

      {/* Real Sales Velocity Line Chart for this SKU */}
      <VelocityChart
        skuId={sku.id}
        title={`Sales Velocity: Expected vs. Actual for ${sku.name}`}
        subtitle="Expected hourly sales pattern compared to actual POS checkout logs over the last 24 open hours."
      />

      {/* Historical Audit Actions */}
      <div className="rounded-xl border border-scout-border bg-scout-surface p-5">
        <div className="mb-4">
          <h3 className="text-base font-semibold text-zinc-900">
            Past Audit &amp; Reconciliation History
          </h3>
          <p className="text-xs text-scout-muted">
            All supervisor inspections, restocks, and damage write-offs logged for this product.
          </p>
        </div>

        {audit_history.length === 0 ? (
          <div className="rounded-lg border border-dashed border-zinc-200 p-6 text-center text-sm text-scout-muted">
            No audit reconciliations have been recorded yet for this product.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-50 text-xs uppercase text-scout-muted">
                <tr>
                  <th className="p-3">Action</th>
                  <th className="p-3">Summary</th>
                  <th className="p-3">Staff Associate</th>
                  <th className="p-3">Units Adjusted</th>
                  <th className="p-3 text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {audit_history.map((item) => (
                  <tr key={item.id} className="border-t border-scout-border">
                    <td className="p-3">
                      <Badge
                        tone={
                          item.action === "restocked"
                            ? "success"
                            : item.action === "damaged"
                            ? "alert"
                            : "neutral"
                        }
                      >
                        {item.action}
                      </Badge>
                    </td>
                    <td className="p-3 text-zinc-800">{item.summary}</td>
                    <td className="p-3 text-zinc-600">
                      {item.associate || "Unassigned"}
                    </td>
                    <td className="p-3 font-mono">
                      {item.units !== null && item.units !== undefined
                        ? item.units
                        : "-"}
                    </td>
                    <td className="p-3 text-right text-xs text-scout-muted">
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}
