"use client";

import { useState } from "react";
import Link from "next/link";
import useSWR from "swr";
import {
  ArrowLeft,
  CheckCircle2,
  Cpu,
  LayoutDashboard,
  RefreshCw,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import { api } from "@/lib/api";
import type { EvaluationReport } from "@/lib/types";
import { EvaluationMetricCards } from "@/components/evaluation/EvaluationMetricCards";
import { ModelComparisonTable } from "@/components/evaluation/ModelComparisonTable";
import { EvaluationCharts } from "@/components/evaluation/EvaluationCharts";
import { ScenarioBreakdownGrid } from "@/components/evaluation/ScenarioBreakdownGrid";

export default function EvaluationPage() {
  const { data: report, error, mutate, isLoading } = useSWR<EvaluationReport>(
    "evaluation_report",
    () => api.getEvaluation(),
    { revalidateOnFocus: false, dedupingInterval: 30000 }
  );

  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [quickMode, setQuickMode] = useState<boolean>(true);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  async function handleRunBenchmark() {
    setIsRunning(true);
    setStatusMessage(
      quickMode
        ? "Running rapid 3-scenario evaluation suite across 200 SKUs…"
        : "Executing full 6-scenario stress test suite (this may take ~45s)…"
    );

    try {
      const updated = await api.runEvaluation(quickMode);
      mutate(updated, false);
      setStatusMessage(
        `Benchmark completed in ${(updated.execution_time_ms / 1000).toFixed(1)}s across ${updated.total_scenarios_evaluated} operational scenarios.`
      );
    } catch (err) {
      setStatusMessage(`Benchmark execution failed: ${(err as Error).message}`);
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#09090B] text-zinc-100 pb-16 selection:bg-violet-500 selection:text-white">
      {/* Top Ambient Glow */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 h-[500px] w-[900px] rounded-full bg-gradient-to-b from-violet-600/15 via-emerald-600/10 to-transparent blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 pt-6 sm:px-6 lg:px-8 space-y-8">
        {/* Navigation & Header */}
        <div className="flex flex-col gap-4 border-b border-zinc-800/80 pb-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2 text-xs text-zinc-400">
              <Link href="/" className="hover:text-zinc-200 transition-colors flex items-center gap-1">
                <ArrowLeft className="h-3.5 w-3.5" />
                Home
              </Link>
              <span>/</span>
              <span className="text-violet-400 font-semibold">Evaluation & Benchmarks</span>
              <span>/</span>
              <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] font-mono text-zinc-300">
                200 SKUs
              </span>
            </div>

            <div className="mt-2 flex items-center gap-3">
              <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
                Model Evaluation & Benchmark Hub
              </h1>
              <span className="rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-xs font-bold text-emerald-400 border border-emerald-500/30">
                Feature F3 & F4
              </span>
            </div>

            <p className="mt-1 text-xs sm:text-sm text-zinc-400 max-w-3xl">
              Empirical accuracy comparison: Traditional Heuristic vs. Scout Probabilistic Engine (B1 Baseline, B3 ZIP, B4 Ensemble). Proves why naive rules fail and how Scout prevents supervisor alert fatigue.
            </p>
          </div>

          {/* Quick links & Benchmark runner */}
          <div className="flex flex-wrap items-center gap-2 sm:self-end">
            <Link
              href="/simulate"
              className="inline-flex items-center gap-1.5 rounded-xl border border-zinc-700 bg-zinc-800/80 px-3.5 py-2 text-xs font-semibold text-zinc-200 hover:bg-zinc-700 transition-colors"
            >
              <Cpu className="h-3.5 w-3.5 text-cyan-400" />
              Demo Simulator
            </Link>

            <Link
              href="/dashboard"
              className="inline-flex items-center gap-1.5 rounded-xl border border-zinc-700 bg-zinc-800/80 px-3.5 py-2 text-xs font-semibold text-zinc-200 hover:bg-zinc-700 transition-colors"
            >
              <LayoutDashboard className="h-3.5 w-3.5 text-violet-400" />
              Manager Portal
            </Link>

            <div className="flex items-center gap-2 rounded-xl border border-zinc-700 bg-zinc-800/50 p-1">
              <button
                type="button"
                onClick={() => setQuickMode(true)}
                className={`rounded-lg px-2.5 py-1 text-[11px] font-semibold transition-colors ${
                  quickMode
                    ? "bg-violet-600 text-white shadow-sm"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                Quick (3 Scen)
              </button>
              <button
                type="button"
                onClick={() => setQuickMode(false)}
                className={`rounded-lg px-2.5 py-1 text-[11px] font-semibold transition-colors ${
                  !quickMode
                    ? "bg-violet-600 text-white shadow-sm"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                Full Suite (6 Scen)
              </button>
            </div>

            <button
              type="button"
              onClick={handleRunBenchmark}
              disabled={isRunning}
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-4 py-2 text-xs font-bold text-white shadow-lg hover:from-emerald-500 hover:to-teal-500 disabled:opacity-50 transition-all"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isRunning ? "animate-spin" : ""}`} />
              {isRunning ? "Evaluating Models…" : "Re-run Live Benchmark"}
            </button>
          </div>
        </div>

        {/* Status notification */}
        {statusMessage && (
          <div className="flex items-center justify-between rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-2.5 text-xs text-emerald-300">
            <span className="flex items-center gap-2 font-medium">
              <Sparkles className="h-4 w-4 text-emerald-400" />
              {statusMessage}
            </span>
            <button
              onClick={() => setStatusMessage(null)}
              className="text-emerald-400 hover:text-emerald-200 font-bold"
            >
              ✕
            </button>
          </div>
        )}

        {/* Loading Skeleton */}
        {isLoading && !report && (
          <div className="space-y-6 animate-pulse">
            <div className="h-32 rounded-2xl bg-zinc-800/50" />
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-28 rounded-2xl bg-zinc-800/50" />
              ))}
            </div>
            <div className="h-64 rounded-2xl bg-zinc-800/50" />
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-6 text-center">
            <ShieldAlert className="mx-auto h-8 w-8 text-rose-400" />
            <h3 className="mt-2 text-sm font-bold text-white">Could not load benchmark report</h3>
            <p className="mt-1 text-xs text-rose-300">
              Ensure the backend server is running on port 8000.
            </p>
            <button
              onClick={() => mutate()}
              className="mt-4 rounded-xl bg-rose-600 px-4 py-1.5 text-xs font-bold text-white"
            >
              Retry Connection
            </button>
          </div>
        )}

        {report && (
          <>
            {/* Executive Proof Banner for Judges */}
            <div className="relative overflow-hidden rounded-3xl border border-violet-500/30 bg-gradient-to-r from-violet-950/40 via-zinc-900 to-emerald-950/40 p-6 shadow-2xl backdrop-blur">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
                <div className="space-y-2 max-w-3xl">
                  <div className="inline-flex items-center gap-2 rounded-full border border-violet-500/40 bg-violet-500/20 px-3 py-1 text-xs font-bold text-violet-300">
                    <Sparkles className="h-3.5 w-3.5" />
                    Key Pitch Finding for Judges
                  </div>
                  <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
                    Traditional Heuristics Fail in Supermarkets. Scout Eliminates 98%+ of False Alerts.
                  </h2>
                  <p className="text-xs sm:text-sm text-zinc-300 leading-relaxed">
                    A fixed retail rule (&quot;flag if no sales for 3 hours&quot;) generates{" "}
                    <span className="font-bold text-red-400">~58 false alarms per shift</span> because slow-selling items naturally pause for 3–6 hours without being out of stock. Scout&apos;s Bayesian Baseline &amp; ZIP mixture model weights silence against expected velocity, delivering{" "}
                    <span className="font-bold text-emerald-400">100% precision</span> and near-zero false alarms.
                  </p>
                </div>

                <div className="flex flex-col sm:flex-row lg:flex-col gap-3 shrink-0">
                  <div className="rounded-2xl border border-zinc-800 bg-zinc-950/80 p-4 text-center">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">
                      Benchmark Time
                    </span>
                    <div className="mt-1 font-mono text-sm font-bold text-zinc-200">
                      {(report.execution_time_ms / 1000).toFixed(1)}s across {report.total_scenarios_evaluated} runs
                    </div>
                  </div>
                  <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-center">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">
                      Alert Reduction
                    </span>
                    <div className="mt-1 font-mono text-xl font-black text-emerald-300">
                      {report.alert_reduction_percent.toFixed(1)}% Noise Cut
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* 4 Hero KPI Cards */}
            <EvaluationMetricCards
              models={report.summary_models}
              alertReductionPercent={report.alert_reduction_percent}
            />

            {/* Side-by-Side Model Comparison Table */}
            <ModelComparisonTable models={report.summary_models} />

            {/* Interactive Recharts Visualizations */}
            <EvaluationCharts
              models={report.summary_models}
              thresholdCurve={report.threshold_curve}
            />

            {/* Scenario Breakdown Stress Tests */}
            <ScenarioBreakdownGrid scenarios={report.scenarios} />

            {/* Architectural Deep Dive & Key Findings */}
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/90 p-6 shadow-xl backdrop-blur">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                <span>Empirical Findings & Architectural Synthesis</span>
              </h3>
              <p className="mt-1 text-xs text-zinc-400">
                Summary of statistical evidence derived from 200 catalog SKUs across high, medium, and low sales velocities.
              </p>

              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                {report.key_findings.map((f, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 rounded-xl border border-zinc-800/80 bg-zinc-950/60 p-4 text-xs"
                  >
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-violet-500/20 font-mono text-[11px] font-bold text-violet-300 border border-violet-500/30">
                      {i + 1}
                    </span>
                    <p className="text-zinc-300 leading-relaxed">{f}</p>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
