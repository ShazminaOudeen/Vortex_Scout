"use client";
import { AnomalyTable } from "@/components/dashboard/AnomalyTable";
import { MetricCards } from "@/components/dashboard/MetricCards";
import { VelocityChart } from "@/components/dashboard/VelocityChart";
import { useAnomalies, useMetrics } from "@/hooks/useAnomalies";

// TODO(Task 3): category breakdown bar chart + recent reconciliations feed.
export default function DashboardPage() {
  const { data: metrics } = useMetrics();
  const { data: anomalies } = useAnomalies();
  return (
    <main className="mx-auto max-w-6xl space-y-6 p-6">
      <h1 className="text-2xl font-bold">Store Manager Dashboard</h1>
      {metrics && <MetricCards m={metrics} />}
      <VelocityChart />
      {anomalies && <AnomalyTable rows={anomalies} />}
    </main>
  );
}
