// Fallback data so frontend work is never blocked on the backend.
// Hooks fall back to this when the API is unreachable.
import type { Anomaly, Checklist, DashboardMetrics } from "./types";

export const mockAnomalies: Anomaly[] = [
  {
    id: "a1", sku_id: "s1", sku_name: "Munchee Super Cream Cracker 490g",
    category: "Biscuits & Confectionery", aisle: "03", bay: "3B",
    ledger_stock: 70, hours_since_last_sale: 14, p_void: 0.93,
    status: "open", detected_at: new Date().toISOString(),
  },
  {
    id: "a2", sku_id: "s2", sku_name: "Highland Fresh Milk 1L",
    category: "Chilled Dairy", aisle: "05", bay: "5A",
    ledger_stock: 32, hours_since_last_sale: 9, p_void: 0.88,
    status: "open", detected_at: new Date().toISOString(),
  },
  {
    id: "a3", sku_id: "s3", sku_name: "Anchor Full Cream Milk Powder 400g",
    category: "Chilled Dairy", aisle: "05", bay: "5C",
    ledger_stock: 41, hours_since_last_sale: 11, p_void: 0.81,
    status: "open", detected_at: new Date().toISOString(),
  },
];

export const mockChecklist: Checklist = {
  briefing:
    "Good morning! 3 high-probability voids detected across Aisles 03 & 05 before peak trade.",
  estimated_minutes: 3,
  groups: [
    { aisle: "03", title: "Aisle 03 — Confectionery & Biscuits", items: [mockAnomalies[0]] },
    { aisle: "05", title: "Aisle 05 — Chilled Dairy", items: [mockAnomalies[1], mockAnomalies[2]] },
  ],
};

export const mockMetrics: DashboardMetrics = {
  revenue_recovered_lkr: 482500,
  active_voids: 6,
  audit_completion_rate: 0.94,
  iri_rate: 0.048,
  category_breakdown: [
    { category: "Chilled Dairy", share: 38 },
    { category: "Biscuits & Confectionery", share: 26 },
    { category: "Dry Staples", share: 18 },
    { category: "Other", share: 18 },
  ],
};
