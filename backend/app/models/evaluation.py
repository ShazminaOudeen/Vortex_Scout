from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class ModelMetrics(BaseModel):
    model_name: str
    display_name: str
    description: str
    precision: float = Field(..., description="TP / (TP + FP)")
    recall: float = Field(..., description="TP / (TP + FN)")
    f1_score: float = Field(..., description="Harmonic mean of precision and recall")
    false_positive_rate: float = Field(..., description="FP / (FP + TN)")
    accuracy: float = Field(..., description="(TP + TN) / Total")
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int
    alert_count: int = Field(..., description="Total alerts raised: TP + FP")
    false_alarms_per_shift: float = Field(..., description="Estimated daily false alarms in a standard 200-SKU shift")


class ScenarioModelResult(BaseModel):
    model_key: str
    model_name: str
    detected: bool = Field(..., description="Whether the true void was detected")
    false_alarms: int = Field(..., description="Number of healthy SKUs falsely flagged")
    precision: float
    recall: float
    flagged_skus: list[str]


class ScenarioEvaluation(BaseModel):
    id: str
    name: str
    category: str
    description: str
    void_sku_id: str | None = None
    void_sku_name: str | None = None
    void_type: str | None = None
    silent_hours: int
    total_skus: int = 200
    model_results: dict[str, ScenarioModelResult]


class ThresholdPoint(BaseModel):
    threshold: float
    precision: float
    recall: float
    f1: float
    false_positive_rate: float


class EvaluationReport(BaseModel):
    generated_at: str
    execution_time_ms: float
    total_scenarios_evaluated: int
    summary_models: list[ModelMetrics]
    scenarios: list[ScenarioEvaluation]
    threshold_curve: list[ThresholdPoint]
    key_findings: list[str]
    alert_reduction_percent: float
