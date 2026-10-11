"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { useSkus } from "@/hooks/useAnomalies";
import { formatLKR } from "@/lib/utils";

type FilterTab = "all" | "critical" | "reconciled";

export default function InventoryPage() {
  const { data: skus, isLoading } = useSkus();
  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState<FilterTab>("all");

  const counts = useMemo(() => {
    if (!skus) return { all: 0, critical: 0, reconciled: 0 };
    return {
      all: skus.length,
      critical: skus.filter((s) => s.has_open_anomaly && s.p_void >= 0.75).length,
      reconciled: skus.filter((s) => s.reconciled_today || s.anomaly_status !== "open" && s.anomaly_status).length,
    };
  }, [skus]);

  const filteredSkus = useMemo(() => {
    if (!skus) return [];
    return skus.filter((s) => {
      // Tab filter
      if (activeTab === "critical" && !(s.has_open_anomaly && s.p_void >= 0.75)) {
        return false;
      }
      if (
        activeTab === "reconciled" &&
        !(s.reconciled_today || (s.anomaly_status !== "open" && s.anomaly_status))
      ) {
        return false;
      }

      // Search query filter
      if (!search.trim()) return true;
      const q = search.toLowerCase();
      return (
        s.name.toLowerCase().includes(q) ||
        s.barcode.toLowerCase().includes(q) ||
        s.category.toLowerCase().includes(q) ||
        s.id.toLowerCase().includes(q)
      );
    });
  }, [skus, activeTab, search]);

  return (
    <main className="mx-auto max-w-6xl space-y-5 p-6">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">
            SKU Catalogue &amp; Anomaly Explorer
          </h1>
          <p className="text-sm text-scout-muted">
            Monitor real-time shelf void probabilities and stock ledger states across all 200 SKUs.
          </p>
        </div>
        <div className="text-xs text-zinc-500">
          Showing <span className="font-semibold text-zinc-800">{filteredSkus.length}</span> of{" "}
          <span className="font-semibold text-zinc-800">{skus?.length ?? 200}</span> SKUs
        </div>
      </div>

      {/* Filter Tabs & Search Bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex rounded-lg border border-scout-border bg-zinc-50 p-1">
          <button
            type="button"
            onClick={() => setActiveTab("all")}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition ${
              activeTab === "all"
                ? "bg-white text-zinc-900 shadow-sm"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            All Catalogue ({counts.all})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("critical")}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition ${
              activeTab === "critical"
                ? "bg-rose-50 text-rose-700 shadow-sm font-semibold"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-rose-500" />
            Critical Voids ({counts.critical})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("reconciled")}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition ${
              activeTab === "reconciled"
                ? "bg-emerald-50 text-emerald-700 shadow-sm font-semibold"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            Reconciled ({counts.reconciled})
          </button>
        </div>

        <div className="w-full sm:w-80">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by product, barcode, category..."
            className="w-full rounded-lg border border-scout-border bg-white px-3.5 py-2 text-sm shadow-sm focus:border-violet-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto rounded-xl border border-scout-border bg-scout-surface shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-scout-border bg-zinc-50 text-xs uppercase text-scout-muted">
            <tr>
              <th className="p-3.5">Product &amp; Barcode</th>
              <th className="p-3.5">Category</th>
              <th className="p-3.5">Location</th>
              <th className="p-3.5">Ledger</th>
              <th className="p-3.5">Unit Price</th>
              <th className="p-3.5">P(void)</th>
              <th className="p-3.5">Risk Status</th>
              <th className="p-3.5 text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={8} className="p-8 text-center text-sm text-scout-muted">
                  Loading 200-SKU store catalogue...
                </td>
              </tr>
            ) : filteredSkus.length === 0 ? (
              <tr>
                <td colSpan={8} className="p-8 text-center text-sm text-scout-muted">
                  No SKUs matching your search or active filter.
                </td>
              </tr>
            ) : (
              filteredSkus.map((s) => {
                const isCritical = s.has_open_anomaly && s.p_void >= 0.75;
                const isReconciled = s.anomaly_status && s.anomaly_status !== "open";

                return (
                  <tr
                    key={s.id}
                    className="border-t border-scout-border transition hover:bg-zinc-50/60"
                  >
                    <td className="p-3.5">
                      <div className="font-medium text-zinc-900">{s.name}</div>
                      <div className="font-mono text-[11px] text-scout-muted">
                        {s.id} • {s.barcode}
                      </div>
                    </td>
                    <td className="p-3.5 text-zinc-600">{s.category}</td>
                    <td className="p-3.5 text-zinc-600">
                      Aisle {s.aisle} / {s.bay}
                    </td>
                    <td className="p-3.5 font-mono text-zinc-800">
                      {s.ledger_stock} units
                    </td>
                    <td className="p-3.5 font-mono text-zinc-800">
                      {formatLKR(s.unit_price)}
                    </td>
                    <td className="p-3.5 font-mono font-semibold">
                      {s.p_void > 0 ? (
                        <span
                          className={
                            isCritical
                              ? "text-rose-600 font-bold"
                              : "text-amber-600"
                          }
                        >
                          {(s.p_void * 100).toFixed(0)}%
                        </span>
                      ) : (
                        <span className="text-zinc-400">0%</span>
                      )}
                    </td>
                    <td className="p-3.5">
                      {isCritical ? (
                        <Badge tone="alert">Critical Void</Badge>
                      ) : isReconciled ? (
                        <Badge tone="success">
                          {s.anomaly_status === "restocked"
                            ? "Restocked"
                            : s.anomaly_status === "damaged"
                            ? "Damaged"
                            : "False Alarm"}
                        </Badge>
                      ) : (
                        <Badge tone="neutral">Normal</Badge>
                      )}
                    </td>
                    <td className="p-3.5 text-right">
                      <Link
                        href={`/inventory/${s.id}`}
                        className="inline-flex items-center rounded-md border border-zinc-200 bg-white px-2.5 py-1 text-xs font-medium text-zinc-700 shadow-sm hover:border-violet-300 hover:bg-violet-50 hover:text-violet-700"
                      >
                        Details →
                      </Link>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}
