"use client";

import { AlertTriangle, Sparkles, Zap, Shield } from "lucide-react";
import type { ModelMetrics } from "@/lib/types";

interface ModelComparisonTableProps {
  models: ModelMetrics[];
}

export function ModelComparisonTable({ models }: ModelComparisonTableProps) {
  const getBadge = (name: string) => {
    switch (name) {
      case "naive_3h":
        return {
          label: "Flawed (Alert Fatigue)",
          color: "bg-red-500/15 text-red-400 border-red-500/30",
          icon: AlertTriangle,
        };
      case "baseline_b1":
        return {
          label: "Fast & Explainable",
          color: "bg-blue-500/15 text-blue-400 border-blue-500/30",
          icon: Shield,
        };
      case "zip_b3":
        return {
          label: "Strong Zero Separation",
          color: "bg-purple-500/15 text-purple-400 border-purple-500/30",
          icon: Zap,
        };
      case "ensemble_scout":
      default:
        return {
          label: "★ Recommended (Ensemble)",
          color: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
          icon: Sparkles,
        };
    }
  };

  return (
    <div className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/90 shadow-xl backdrop-blur">
      <div className="border-b border-zinc-800/80 px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span>Model Performance Comparison Matrix</span>
            <span className="rounded-full bg-violet-500/20 px-2 py-0.5 text-[11px] font-medium text-violet-300 border border-violet-500/30">
              Evaluated on 200 Catalog SKUs
            </span>
          </h3>
          <p className="text-xs text-zinc-400">
            Side-by-side empirical metrics measured across quiet trading, weekend traffic peaks, and multiple void classes.
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-950/60 text-[11px] font-semibold uppercase tracking-wider text-zinc-400">
              <th className="px-6 py-3.5">Model Architecture</th>
              <th className="px-4 py-3.5 text-center">Precision</th>
              <th className="px-4 py-3.5 text-center">Recall</th>
              <th className="px-4 py-3.5 text-center">F1 Score</th>
              <th className="px-4 py-3.5 text-center">False Positive Rate</th>
              <th className="px-4 py-3.5 text-center">False Alarms / Shift</th>
              <th className="px-6 py-3.5 text-right">Operational Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60 font-medium">
            {models.map((m) => {
              const isWinner = m.model_name === "ensemble_scout";
              const isNaive = m.model_name === "naive_3h";
              const badge = getBadge(m.model_name);
              const BadgeIcon = badge.icon;

              return (
                <tr
                  key={m.model_name}
                  className={`transition-colors duration-150 ${
                    isWinner
                      ? "bg-emerald-950/20 hover:bg-emerald-950/30"
                      : isNaive
                      ? "bg-red-950/10 hover:bg-red-950/20"
                      : "hover:bg-zinc-800/40"
                  }`}
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div
                        className={`flex h-8 w-8 items-center justify-center rounded-lg border ${
                          isWinner
                            ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
                            : isNaive
                            ? "border-red-500/30 bg-red-500/10 text-red-400"
                            : "border-zinc-700 bg-zinc-800 text-zinc-300"
                        }`}
                      >
                        <BadgeIcon className="h-4 w-4" />
                      </div>
                      <div>
                        <div className="font-bold text-white flex items-center gap-2">
                          {m.display_name}
                          {isWinner && (
                            <span className="rounded bg-emerald-500/20 px-1.5 py-0.2 text-[10px] font-semibold text-emerald-400 border border-emerald-500/30">
                              Production
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] text-zinc-400 max-w-sm truncate">
                          {m.description}
                        </div>
                      </div>
                    </div>
                  </td>

                  <td className="px-4 py-4 text-center">
                    <div className="inline-flex flex-col items-center">
                      <span
                        className={`font-mono text-sm font-bold ${
                          isWinner || m.precision >= 0.8
                            ? "text-emerald-400"
                            : isNaive
                            ? "text-red-400"
                            : "text-zinc-200"
                        }`}
                      >
                        {(m.precision * 100).toFixed(1)}%
                      </span>
                      <div className="mt-1 h-1.5 w-16 overflow-hidden rounded-full bg-zinc-800">
                        <div
                          className={`h-full ${
                            isWinner || m.precision >= 0.8
                              ? "bg-emerald-500"
                              : isNaive
                              ? "bg-red-500"
                              : "bg-blue-500"
                          }`}
                          style={{ width: `${Math.max(5, m.precision * 100)}%` }}
                        />
                      </div>
                    </div>
                  </td>

                  <td className="px-4 py-4 text-center">
                    <span className="font-mono text-sm font-bold text-zinc-100">
                      {(m.recall * 100).toFixed(1)}%
                    </span>
                  </td>

                  <td className="px-4 py-4 text-center">
                    <span className="font-mono text-sm font-bold text-zinc-200">
                      {(m.f1_score * 100).toFixed(1)}%
                    </span>
                  </td>

                  <td className="px-4 py-4 text-center">
                    <span
                      className={`font-mono text-sm font-bold ${
                        m.false_positive_rate < 0.01
                          ? "text-emerald-400"
                          : isNaive
                          ? "text-red-400"
                          : "text-amber-400"
                      }`}
                    >
                      {(m.false_positive_rate * 100).toFixed(2)}%
                    </span>
                  </td>

                  <td className="px-4 py-4 text-center">
                    <div className="inline-flex items-center gap-1.5">
                      <span
                        className={`font-mono text-sm font-black ${
                          m.false_alarms_per_shift === 0
                            ? "text-emerald-400"
                            : m.false_alarms_per_shift < 2
                            ? "text-emerald-300"
                            : "text-red-400 font-extrabold"
                        }`}
                      >
                        {m.false_alarms_per_shift.toFixed(1)}
                      </span>
                      <span className="text-[10px] text-zinc-500">alerts/shift</span>
                    </div>
                  </td>

                  <td className="px-6 py-4 text-right">
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold ${badge.color}`}
                    >
                      <BadgeIcon className="h-3 w-3" />
                      {badge.label}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
