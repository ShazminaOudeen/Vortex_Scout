// Keep in sync with backend/app/models/*.py (Pydantic schemas).

export type AnomalyStatus = "open" | "restocked" | "damaged" | "false_alarm";
export type AuditAction = "restocked" | "damaged" | "false_alarm";
export type VoidType = "frozen" | "damaged" | "backroom_stuck" | "shelf_void";

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
  resolved_at?: string | null;
  void_type?: VoidType;
  suggested_action?: AuditAction;
}

export interface ChecklistGroup {
  aisle: string;
  title: string;
  items: Anomaly[];
}

export interface Checklist {
  briefing: string;
  estimated_minutes: number;
  groups: ChecklistGroup[];
}

export interface ReconcilePayload {
  anomaly_id: string;
  action: AuditAction;
  associate?: string;
  units?: number;
}

export interface ReconcileResult {
  ok: boolean;
  already_resolved: boolean;
  status: AnomalyStatus;
  ledger_stock: number | null;
  ledger_adjustment: number;
}

export interface AuditStats {
  total: number;
  restocked: number;
  damaged: number;
  false_alarm: number;
  false_alarm_rate: number;
}

export interface IngestError {
  index: number;
  message: string;
}

export interface IngestResult {
  ingested: number;
  rejected: number;
  errors: IngestError[];
}

export interface DashboardMetrics {
  revenue_recovered_lkr: number;
  active_voids: number;
  audit_completion_rate: number;
  iri_rate: number;
  category_breakdown: { category: string; share: number }[];
}
