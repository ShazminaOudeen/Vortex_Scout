"use client";

import { useState } from "react";
import Link from "next/link";
import { AnomalyTable } from "@/components/dashboard/AnomalyTable";
import { CategoryRiskChart } from "@/components/dashboard/CategoryRiskChart";
import { MetricCards } from "@/components/dashboard/MetricCards";
import { RecentReconciliationsFeed } from "@/components/dashboard/RecentReconciliationsFeed";
import { VelocityChart } from "@/components/dashboard/VelocityChart";
import { useAnomalies, useMetrics } from "@/hooks/useAnomalies";

export default function DashboardPage() {
  const { data: metrics } = useMetrics();
  const { data: anomalies } = useAnomalies();

  // Selected anomaly for the velocity chart; default to the first anomaly
  const [selectedAnomalyId, setSelectedAnomalyId] = useState<string | undefined>(undefined);

  const activeAnomalyId =
    selectedAnomalyId ?? (anomalies && anomalies.length > 0 ? anomalies[0].id : undefined);

  return (
    <main className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Store Manager Portal</h1>
          <p className="text-sm text-scout-muted">
            Overview of phantom inventory, real sales velocity drops, and floor audits.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/inventory"
            className="rounded-lg border border-scout-border bg-white px-3 py-1.5 text-xs font-semibold text-zinc-700 shadow-sm hover:bg-zinc-50 transition-colors"
          >
            Inventory
          </Link>
          <Link
            href="/evaluation"
            className="rounded-lg border border-teal-500/30 bg-teal-50 px-3 py-1.5 text-xs font-semibold text-teal-700 shadow-sm hover:bg-teal-100 transition-colors"
          >
            Model Evaluation
          </Link>
          <Link
            href="/simulate"
            className="rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-zinc-800 transition-colors"
          >
            Simulator
          </Link>
        </div>
      </div>

      {/* E1: Real KPIs */}
      {metrics && <MetricCards m={metrics} />}

      {/* E2: Expected vs Actual Sales Velocity Chart with SKU selector */}
      <div className="space-y-3">
        {anomalies && anomalies.length > 0 && (
          <div className="flex items-center gap-2">
            <label htmlFor="anomaly-select" className="text-xs font-medium text-zinc-600">
              Inspect Anomaly:
            </label>
            <select
              id="anomaly-select"
              value={activeAnomalyId}
              onChange={(e) => setSelectedAnomalyId(e.target.value)}
              className="rounded-lg border border-scout-border bg-white px-3 py-1.5 text-xs font-medium text-zinc-800 shadow-sm focus:border-violet-500 focus:outline-none"
            >
              {anomalies.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.sku_name} — P(void) {(a.p_void * 100).toFixed(0)}% ({a.status})
                </option>
              ))}
            </select>
          </div>
        )}
        <VelocityChart anomalyId={activeAnomalyId} />
      </div>

      {/* Grid: E3 High-Risk Category Chart & E4 Recent Reconciliations Feed */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <CategoryRiskChart data={metrics?.category_breakdown ?? []} />
        <RecentReconciliationsFeed limit={10} />
      </div>

      {/* Anomaly Table */}
      {anomalies && <AnomalyTable rows={anomalies} />}
    </main>
  );
}
