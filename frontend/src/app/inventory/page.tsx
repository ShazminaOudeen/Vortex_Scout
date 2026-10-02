"use client";
import { useState } from "react";
import { AnomalyTable } from "@/components/dashboard/AnomalyTable";
import { useAnomalies } from "@/hooks/useAnomalies";

// TODO(Task 3): full 200-SKU table (needs a /api/v1/skus endpoint), filter tabs, risk badges.
export default function InventoryPage() {
  const { data } = useAnomalies();
  const [q, setQ] = useState("");
  const rows = (data ?? []).filter((r) => r.sku_name.toLowerCase().includes(q.toLowerCase()));
  return (
    <main className="mx-auto max-w-6xl space-y-4 p-6">
      <h1 className="text-2xl font-bold">SKU Inventory &amp; Anomaly Explorer</h1>
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Search product (Anchor, Munchee, Highland…)"
        className="w-full rounded-lg border border-scout-border bg-white p-3 text-sm"
      />
      <AnomalyTable rows={rows} />
    </main>
  );
}
