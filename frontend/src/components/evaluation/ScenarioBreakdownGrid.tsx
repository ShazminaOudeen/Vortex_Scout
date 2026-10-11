"use client";

import { AlertCircle, Sparkles, Box, Shield, Zap } from "lucide-react";
import type { ScenarioEvaluation } from "@/lib/types";

interface ScenarioBreakdownGridProps {
  scenarios: ScenarioEvaluation[];
}

export function ScenarioBreakdownGrid({ scenarios }: ScenarioBreakdownGridProps) {
  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span>Operational Scenario Stress Tests</span>
            <span className="rounded-full bg-violet-500/20 px-2 py-0.5 text-[11px] font-medium text-violet-300 border border-violet-500/30">
              {scenarios.length} Conditions Tested
            </span>
          </h3>
          <p className="text-xs text-zinc-400">
            Real-world simulations evaluating how each algorithm responds to different inventory dynamics and footfall regimes.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {scenarios.map((sc) => {
          const isVoidScenario = Boolean(sc.void_sku_id);
          const naiveRes = sc.model_results["naive_3h"];
          const baseRes = sc.model_results["baseline_b1"];
          const zipRes = sc.model_results["zip_b3"];
          const scoutRes = sc.model_results["ensemble_scout"];

          return (
            <div
              key={sc.id}
              className="flex flex-col justify-between rounded-2xl border border-zinc-800 bg-zinc-900/90 p-5 shadow-lg backdrop-blur transition-all duration-200 hover:border-zinc-700 hover:shadow-xl"
            >
              <div>
                <div className="flex items-center justify-between gap-2">
                  <span className="rounded-full bg-zinc-800 px-2.5 py-0.5 text-[10px] font-semibold text-zinc-300 border border-zinc-700">
                    {sc.category}
                  </span>
                  {isVoidScenario ? (
                    <span className="rounded-full bg-rose-500/20 px-2 py-0.5 text-[10px] font-bold text-rose-300 border border-rose-500/30">
                      {sc.silent_hours}h Silent Void
                    </span>
                  ) : (
                    <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-300 border border-emerald-500/30">
                      Clean Store (0 Voids)
                    </span>
                  )}
                </div>

                <h4 className="mt-3 text-sm font-bold text-white">
                  {sc.name}
                </h4>
                <p className="mt-1 text-xs text-zinc-400 leading-relaxed">
                  {sc.description}
                </p>

                {sc.void_sku_name && (
                  <div className="mt-3 flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-950/60 p-2.5 text-xs">
                    <Box className="h-4 w-4 text-violet-400 shrink-0" />
                    <div className="truncate">
                      <span className="text-[10px] uppercase font-bold text-zinc-500">Target Product: </span>
                      <span className="font-semibold text-zinc-200">{sc.void_sku_name}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Model outcomes */}
              <div className="mt-4 pt-3 border-t border-zinc-800/80 space-y-2 text-xs">
                {/* Scout Ensemble */}
                <div className="flex items-center justify-between rounded-lg bg-emerald-950/25 px-2.5 py-1.5 border border-emerald-500/30">
                  <span className="font-semibold text-emerald-300 flex items-center gap-1.5 text-[11px]">
                    <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
                    Scout Ensemble
                  </span>
                  <div className="flex items-center gap-2 text-[11px]">
                    <span className="font-bold text-emerald-400">
                      {scoutRes?.detected ? "✓ Void Caught" : "✓ No False Alarm"}
                    </span>
                    <span className="text-zinc-500 font-mono text-[10px]">
                      ({scoutRes?.false_alarms || 0} FA)
                    </span>
                  </div>
                </div>

                {/* ZIP Model */}
                <div className="flex items-center justify-between rounded-lg bg-purple-950/20 px-2.5 py-1.5 border border-purple-500/20">
                  <span className="font-semibold text-purple-300 flex items-center gap-1.5 text-[11px]">
                    <Zap className="h-3.5 w-3.5 text-purple-400" />
                    ZIP Model (B3)
                  </span>
                  <div className="flex items-center gap-2 text-[11px]">
                    <span className="font-bold text-purple-300">
                      {zipRes?.detected ? "✓ Detected" : "Clear"}
                    </span>
                    <span className="text-zinc-500 font-mono text-[10px]">
                      ({zipRes?.false_alarms || 0} FA)
                    </span>
                  </div>
                </div>

                {/* Baseline B1 */}
                <div className="flex items-center justify-between rounded-lg bg-blue-950/20 px-2.5 py-1.5 border border-blue-500/20">
                  <span className="font-semibold text-blue-300 flex items-center gap-1.5 text-[11px]">
                    <Shield className="h-3.5 w-3.5 text-blue-400" />
                    Baseline (B1)
                  </span>
                  <div className="flex items-center gap-2 text-[11px]">
                    <span className="font-bold text-blue-300">
                      {baseRes?.detected ? "✓ Detected" : "Clear"}
                    </span>
                    <span className="text-zinc-500 font-mono text-[10px]">
                      ({baseRes?.false_alarms || 0} FA)
                    </span>
                  </div>
                </div>

                {/* Naive 3h Rule */}
                <div className="flex items-center justify-between rounded-lg bg-red-950/20 px-2.5 py-1.5 border border-red-500/20">
                  <span className="font-semibold text-red-300 flex items-center gap-1.5 text-[11px]">
                    <AlertCircle className="h-3.5 w-3.5 text-red-400" />
                    Simple 3h Rule
                  </span>
                  <div className="flex items-center gap-2 text-[11px]">
                    <span className="font-bold text-red-400">
                      {naiveRes?.false_alarms && naiveRes.false_alarms > 10
                        ? `⚠ ${naiveRes.false_alarms} False Alarms`
                        : `${naiveRes?.false_alarms || 0} FA`}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
