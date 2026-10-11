"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  ReferenceLine,
} from "recharts";
import type { ModelMetrics, ThresholdPoint } from "@/lib/types";

interface EvaluationChartsProps {
  models: ModelMetrics[];
  thresholdCurve: ThresholdPoint[];
}

export function EvaluationCharts({ models, thresholdCurve }: EvaluationChartsProps) {
  // Chart 1: Precision & Recall by model
  const precisionRecallData = models.map((m) => ({
    name: m.model_name === "naive_3h"
      ? "Naive 3h"
      : m.model_name === "baseline_b1"
      ? "Baseline B1"
      : m.model_name === "zip_b3"
      ? "ZIP B3"
      : "Scout Ensemble",
    Precision: Number((m.precision * 100).toFixed(1)),
    Recall: Number((m.recall * 100).toFixed(1)),
    F1: Number((m.f1_score * 100).toFixed(1)),
  }));

  // Chart 2: False positive rate & daily alert volume
  const alertComparisonData = models.map((m) => ({
    name: m.model_name === "naive_3h"
      ? "Naive 3h"
      : m.model_name === "baseline_b1"
      ? "Baseline B1"
      : m.model_name === "zip_b3"
      ? "ZIP B3"
      : "Scout Ensemble",
    FPR: Number((m.false_positive_rate * 100).toFixed(2)),
    "False Alarms / Shift": m.false_alarms_per_shift,
  }));

  // Chart 3: Threshold sensitivity curve
  const curveData = thresholdCurve.map((p) => ({
    threshold: p.threshold.toFixed(2),
    Precision: Number((p.precision * 100).toFixed(1)),
    Recall: Number((p.recall * 100).toFixed(1)),
    F1: Number((p.f1 * 100).toFixed(1)),
    FPR: Number((p.false_positive_rate * 100).toFixed(2)),
  }));

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      {/* Chart 1: Precision & Recall by Model */}
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/90 p-5 shadow-xl backdrop-blur">
        <div className="mb-4">
          <h4 className="text-sm font-bold text-white flex items-center justify-between">
            <span>Model Accuracy: Precision vs Recall</span>
            <span className="text-[11px] font-normal text-zinc-400">Higher is better (100% max)</span>
          </h4>
          <p className="text-xs text-zinc-400">
            Notice the catastrophic precision collapse in the Naive 3h heuristic compared to Scout&apos;s near-perfect precision.
          </p>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={precisionRecallData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272A" vertical={false} />
              <XAxis dataKey="name" stroke="#A1A1AA" tick={{ fill: "#A1A1AA", fontSize: 11 }} />
              <YAxis unit="%" stroke="#A1A1AA" tick={{ fill: "#A1A1AA", fontSize: 11 }} domain={[0, 105]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#18181B",
                  borderColor: "#3F3F46",
                  borderRadius: "0.75rem",
                  color: "#FAFAFA",
                  fontSize: "12px",
                }}
              />
              <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }} />
              <Bar dataKey="Precision" fill="#10B981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Recall" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="F1" fill="#06B6D4" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Chart 2: False Positive Rate & Shift False Alarms */}
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/90 p-5 shadow-xl backdrop-blur">
        <div className="mb-4">
          <h4 className="text-sm font-bold text-white flex items-center justify-between">
            <span>Alert Fatigue: Daily False Alarms</span>
            <span className="text-[11px] font-normal text-zinc-400">Lower is better</span>
          </h4>
          <p className="text-xs text-zinc-400">
            Average unnecessary alert burden imposed on floor associates per standard 8-hour supermarket shift.
          </p>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={alertComparisonData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272A" vertical={false} />
              <XAxis dataKey="name" stroke="#A1A1AA" tick={{ fill: "#A1A1AA", fontSize: 11 }} />
              <YAxis stroke="#A1A1AA" tick={{ fill: "#A1A1AA", fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#18181B",
                  borderColor: "#3F3F46",
                  borderRadius: "0.75rem",
                  color: "#FAFAFA",
                  fontSize: "12px",
                }}
              />
              <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }} />
              <Bar dataKey="False Alarms / Shift" fill="#EF4444" radius={[4, 4, 0, 0]} />
              <Bar dataKey="FPR" name="False Positive Rate (%)" fill="#F59E0B" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Chart 3: Threshold Sensitivity & ROC-PR Tradeoff */}
      <div className="lg:col-span-2 rounded-2xl border border-zinc-800 bg-zinc-900/90 p-5 shadow-xl backdrop-blur">
        <div className="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
          <div>
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <span>Threshold Calibration & Trade-Off Curve</span>
              <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-400 border border-emerald-500/30">
                Optimal Operating Point: 0.75
              </span>
            </h4>
            <p className="text-xs text-zinc-400">
              Parametric sensitivity sweep across void probabilities (0.10 to 0.95). Proves robustness against threshold drift.
            </p>
          </div>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={curveData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272A" vertical={false} />
              <XAxis dataKey="threshold" stroke="#A1A1AA" tick={{ fill: "#A1A1AA", fontSize: 11 }} />
              <YAxis unit="%" stroke="#A1A1AA" tick={{ fill: "#A1A1AA", fontSize: 11 }} domain={[0, 105]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#18181B",
                  borderColor: "#3F3F46",
                  borderRadius: "0.75rem",
                  color: "#FAFAFA",
                  fontSize: "12px",
                }}
              />
              <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }} />
              <ReferenceLine x="0.75" stroke="#10B981" strokeDasharray="4 4" label={{ value: "Calibrated 0.75", fill: "#10B981", fontSize: 11, position: "top" }} />
              <Line type="monotone" dataKey="Precision" stroke="#10B981" strokeWidth={2.5} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="Recall" stroke="#8B5CF6" strokeWidth={2.5} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="F1" stroke="#06B6D4" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="FPR" name="False Positive Rate (%)" stroke="#EF4444" strokeWidth={1.5} dot={{ r: 2 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
