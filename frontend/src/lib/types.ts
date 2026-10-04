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
  unit_price: number;
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
  resolved_at?: string | null; // API always sends it (null while open); optional so mocks needn't
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
  units?: number; // >= 0; for "damaged" this many units are written off the ledger
}

export interface ReconcileResult {
  ok: boolean;
  already_resolved: boolean; // true on a double tap: nothing changed, no 2nd audit row
  status: AnomalyStatus;
  ledger_stock: number | null; // SKU ledger after this call
  ledger_adjustment: number; // units written off by this call (<= 0)
}

export interface AuditStats {
  total: number;
  restocked: number;
  damaged: number;
  false_alarm: number;
  false_alarm_rate: number; // 0..1
}

export interface IngestError {
  index: number; // position of the row in the submitted batch
  message: string;
}

// POST /api/v1/pos/stream (and /pos/stream/csv). HTTP 422 with this same body if every row was rejected.
export interface IngestResult {
  ingested: number;
  rejected: number;
  errors: IngestError[]; // capped at 100; `rejected` is the full count
}

export interface DashboardMetrics {
  revenue_recovered_lkr: number;
  active_voids: number;
  audit_completion_rate: number; // 0..1
  iri_rate: number; // inventory record inaccuracy 0..1
  category_breakdown: { category: string; share: number }[];
}
