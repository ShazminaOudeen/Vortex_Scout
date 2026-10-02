// Keep in sync with backend/app/models/*.py (Pydantic schemas).

export type AnomalyStatus = "open" | "restocked" | "damaged" | "false_alarm";
export type AuditAction = "restocked" | "damaged" | "false_alarm";

export interface Sku {
  id: string;
  barcode: string;
  name: string;
  category: string;
  aisle: string;
  bay: string;
  ledger_stock: number;
  unit_cost: number;
}

export interface Anomaly {
  id: string;
  sku_id: string;
  sku_name: string;
  category: string;
  aisle: string;
  bay: string;
  ledger_stock: number;
  hours_since_last_sale: number;
  p_void: number; // 0..1, flagged when >= 0.75
  status: AnomalyStatus;
  detected_at: string; // ISO timestamp
}

export interface ChecklistGroup {
  aisle: string;
  title: string; // e.g. "Aisle 03 — Confectionery & Biscuits"
  items: Anomaly[];
}

export interface Checklist {
  briefing: string; // Gemini natural-language summary
  estimated_minutes: number;
  groups: ChecklistGroup[];
}

export interface ReconcilePayload {
  anomaly_id: string;
  action: AuditAction;
  associate?: string;
  units?: number;
}

export interface DashboardMetrics {
  revenue_recovered_lkr: number;
  active_voids: number;
  audit_completion_rate: number; // 0..1
  iri_rate: number; // inventory record inaccuracy 0..1
  category_breakdown: { category: string; share: number }[];
}
