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
  unit_price?: number;
  revenue_at_risk?: number;
  priority_score?: number;
  expected_sales?: number;
  why_flagged?: string;
  priority_level?: "critical" | "high" | "medium" | "low";
}

export interface ItemStructuredAdvice {
  sku_id: string;
  priority: "critical" | "high" | "medium" | "low";
  reason: string;
  suggested_action: AuditAction;
}

export interface ChecklistAgentPlan {
  briefing: string;
  start_aisle: string;
  items: ItemStructuredAdvice[];
}

export interface ChecklistGroup {
  aisle: string;
  title: string;
  items: Anomaly[];
}

export interface Checklist {
  briefing: string;
  estimated_minutes: number;
  total_revenue_at_risk?: number;
  groups: ChecklistGroup[];
  plan?: ChecklistAgentPlan;
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

export interface UndoPayload {
  anomaly_id: string;
  associate?: string;
}

export interface UndoResult {
  ok: boolean;
  reopened: boolean;
  anomaly_id: string;
  status: AnomalyStatus;
  ledger_stock: number | null;
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

export interface AuditFeedItem {
  id: number | string;
  anomaly_id: string;
  sku_id: string;
  sku_name: string;
  category: string;
  aisle: string;
  bay: string;
  action: AuditAction | string;
  associate?: string | null;
  units?: number | null;
  created_at: string;
  summary: string;
}

export interface VelocityPoint {
  timestamp: string;
  hour: string;
  expected: number;
  actual: number;
}

export interface VelocityResponse {
  sku_id: string;
  sku_name: string;
  points: VelocityPoint[];
  has_data: boolean;
}

export interface SkuWithStatus extends Sku {
  p_void: number;
  anomaly_status?: AnomalyStatus | null;
  anomaly_id?: string | null;
  has_open_anomaly: boolean;
  reconciled_today: boolean;
  risk_level: "critical" | "high" | "normal";
}

export interface SkuDetail {
  sku: SkuWithStatus;
  open_anomaly?: Anomaly | null;
  audit_history: AuditFeedItem[];
}

export interface PosTransactionFeedItem {
  id: number | string;
  store_id: string;
  sku_id: string;
  sku_name: string;
  timestamp: string;
  quantity: number;
  unit_price: number;
  total_amount: number;
  aisle: string;
  bay: string;
}

export interface DetectionAlertItem {
  sku_id: string;
  sku_name: string;
  aisle: string;
  bay: string;
  category: string;
  p_void: number;
  silent_hours: number;
  expected_sales: number;
  ledger_stock: number;
  void_type?: VoidType;
  suggested_action?: AuditAction;
  unit_price: number;
  revenue_at_risk: number;
  priority_score: number;
  why_flagged: string;
}

export interface DetectionCalibrationInfo {
  base_threshold: number;
  effective_threshold: number;
  total_audits: number;
  false_alarm_rate: number;
  status: "calibrated" | "insufficient_data" | "default" | string;
  reason?: string;
}

export interface DetectionRunResult {
  flagged: number;
  created: number;
  updated: number;
  cleared: number;
  ledger_zero_skipped?: number;
  threshold: number;
  calibration?: DetectionCalibrationInfo;
  data_as_of?: string;
  alerts: DetectionAlertItem[];
}

export interface ModelMetrics {
  model_name: string;
  display_name: string;
  description: string;
  precision: number;
  recall: number;
  f1_score: number;
  false_positive_rate: number;
  accuracy: number;
  true_positives: number;
  false_positives: number;
  false_negatives: number;
  true_negatives: number;
  alert_count: number;
  false_alarms_per_shift: number;
}

export interface ScenarioModelResult {
  model_key: string;
  model_name: string;
  detected: boolean;
  false_alarms: number;
  precision: number;
  recall: number;
  flagged_skus: string[];
}

export interface ScenarioEvaluation {
  id: string;
  name: string;
  category: string;
  description: string;
  void_sku_id?: string | null;
  void_sku_name?: string | null;
  void_type?: string | null;
  silent_hours: number;
  total_skus: number;
  model_results: Record<string, ScenarioModelResult>;
}

export interface ThresholdPoint {
  threshold: number;
  precision: number;
  recall: number;
  f1: number;
  false_positive_rate: number;
}

export interface EvaluationReport {
  generated_at: string;
  execution_time_ms: number;
  total_scenarios_evaluated: number;
  summary_models: ModelMetrics[];
  scenarios: ScenarioEvaluation[];
  threshold_curve: ThresholdPoint[];
  key_findings: string[];
  alert_reduction_percent: number;
}

