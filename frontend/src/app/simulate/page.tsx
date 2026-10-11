"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Activity,
  PlayCircle,
  RefreshCw,
  Sparkles,
  Zap,
  ArrowLeft,
  ChevronRight,
  ClipboardList,
  LayoutDashboard,
  Boxes,
  Cpu,
  ShieldAlert,
  Flame,
} from "lucide-react";
import { api } from "@/lib/api";
import type { DetectionRunResult } from "@/lib/types";
import { PosTerminal } from "@/components/simulate/PosTerminal";
import { DetectionOutcomeCard } from "@/components/simulate/DetectionOutcomeCard";

export default function SimulatePage() {
  const [log, setLog] = useState<string[]>([]);
  const [isRunningScenario, setIsRunningScenario] = useState<string | null>(null);
  const [isDetecting, setIsDetecting] = useState<boolean>(false);
  const [detectionResult, setDetectionResult] = useState<DetectionRunResult | null>(null);
  const [scenarioNotice, setScenarioNotice] = useState<string | null>(null);

  const pushLog = (m: string) =>
    setLog((l) => [
      ...l.slice(-40),
      `[${new Date().toLocaleTimeString()}] ${m}`,
    ]);

  async function handleInject(
    scenario: "phantom" | "normal" | "reset",
    label: string,
    noticeText: string
  ) {
    setIsRunningScenario(scenario);
    pushLog(`EXECUTING SCENARIO: ${label}…`);
    try {
      const res = await api.injectScenario(scenario);
      pushLog(`SUCCESS: ${JSON.stringify(res)}`);
      setScenarioNotice(noticeText);
    } catch (e) {
      pushLog(`ERROR: ${(e as Error).message}`);
    } finally {
      setIsRunningScenario(null);
    }
  }

  async function handleRunDetection() {
    setIsDetecting(true);
    pushLog("TRIGGER: Running Vortex Scout anomaly detection & Gemini agent…");
    try {
      const res = await api.runDetection();
      setDetectionResult(res);
      pushLog(
        `DETECTION FINISHED: Flagged=${res.flagged}, Created=${res.created}, Updated=${res.updated}, Cleared=${res.cleared}, Threshold=${res.threshold}`
      );
      if (res.flagged > 0) {
        setScenarioNotice(
          `[SCOUT ALERT] ${res.flagged} shelf void(s) detected! Check the Floor Checklist to dispatch floor associates.`
        );
      }
    } catch (e) {
      pushLog(`ERROR RUNNING DETECTION: ${(e as Error).message}`);
    } finally {
      setIsDetecting(false);
    }
  }

  return (
    <main className="min-h-screen bg-scout-night p-4 sm:p-6 lg:p-8 text-zinc-100">
      <div className="mx-auto max-w-7xl space-y-6">
        {/* Top Navigation & Header */}
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-zinc-800 pb-5">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="flex h-9 w-9 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-zinc-100 hover:border-zinc-700 transition-colors"
              title="Return to home portal"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                  <Activity className="h-6 w-6 text-scout-violet" />
                  Simulation &amp; Evaluation Hub
                </h1>
                <span className="rounded-full bg-violet-950/70 border border-violet-500/40 px-2.5 py-0.5 text-xs font-semibold text-violet-300">
                  Feature F1 &amp; F2
                </span>
              </div>
              <p className="text-xs sm:text-sm text-zinc-400 mt-0.5">
                Induce synthetic shelf-void scenarios, stream live register telemetry, and trigger the AI floor agent
              </p>
            </div>
          </div>

          {/* Quick links to existing portals */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <Link
              href="/floor"
              className="flex items-center gap-1.5 rounded-lg border border-violet-500/30 bg-violet-950/40 px-3 py-1.5 font-medium text-violet-300 hover:bg-violet-900/40 transition-colors"
            >
              <ClipboardList className="h-3.5 w-3.5" />
              <span>Floor Checklist</span>
            </Link>
            <Link
              href="/dashboard"
              className="flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-1.5 font-medium text-zinc-300 hover:border-zinc-700 hover:text-white transition-colors"
            >
              <LayoutDashboard className="h-3.5 w-3.5" />
              <span>Manager Portal</span>
            </Link>
            <Link
              href="/inventory"
              className="flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-1.5 font-medium text-zinc-300 hover:border-zinc-700 hover:text-white transition-colors"
            >
              <Boxes className="h-3.5 w-3.5" />
              <span>Inventory</span>
            </Link>
          </div>
        </header>

        {/* Section 1: Scenario Induction Controls */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
              <Cpu className="h-4 w-4 text-scout-violet" />
              Scenario Control Deck
            </h2>
            <span className="text-xs text-zinc-500">
              Interactive triggers for pitch demo
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Scenario 1: Inject Phantom Stockout */}
            <button
              onClick={() =>
                handleInject(
                  "phantom",
                  "Inject Phantom Stockout",
                  "[INJECTION DETECTED] Simulated freeze on Munchee Cracker (s1). POS sales suppressed while ledger says 40 units."
                )
              }
              disabled={Boolean(isRunningScenario)}
              className="group relative flex flex-col justify-between rounded-xl border border-rose-500/30 bg-gradient-to-b from-rose-950/20 to-zinc-900/90 p-4 text-left transition-all hover:border-rose-500/60 hover:shadow-lg hover:shadow-rose-950/30"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20 group-hover:scale-105 transition-transform">
                    <ShieldAlert className="h-5 w-5" />
                  </div>
                  <span className="rounded bg-rose-950/80 px-1.5 py-0.5 font-mono text-[10px] text-rose-300 border border-rose-500/30">
                    SCENARIO A
                  </span>
                </div>
                <h3 className="font-semibold text-sm text-zinc-100 group-hover:text-rose-300 transition-colors">
                  Inject Phantom Stockout
                </h3>
                <p className="mt-1 text-xs text-zinc-400">
                  Zeros sales on Munchee Cracker (<code className="text-rose-400">s1</code>) for 32h while ledger stock remains at 40.
                </p>
              </div>
              <div className="mt-4 flex items-center gap-1 text-[11px] font-medium text-rose-400">
                <span>{isRunningScenario === "phantom" ? "Injecting…" : "Induce void now"}</span>
                <ChevronRight className="h-3 w-3 group-hover:translate-x-1 transition-transform" />
              </div>
            </button>

            {/* Scenario 2: Simulate Normal Peak */}
            <button
              onClick={() =>
                handleInject(
                  "normal",
                  "Simulate Normal Peak",
                  "[SCENARIO NORMAL] Synthetic weekend peak traffic generated across bakery, dairy, and confectionery."
                )
              }
              disabled={Boolean(isRunningScenario)}
              className="group relative flex flex-col justify-between rounded-xl border border-zinc-800 bg-gradient-to-b from-zinc-900 to-zinc-950 p-4 text-left transition-all hover:border-zinc-700 hover:shadow-lg"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 group-hover:scale-105 transition-transform">
                    <Flame className="h-5 w-5" />
                  </div>
                  <span className="rounded bg-zinc-800 px-1.5 py-0.5 font-mono text-[10px] text-zinc-400">
                    SCENARIO B
                  </span>
                </div>
                <h3 className="font-semibold text-sm text-zinc-100 group-hover:text-emerald-300 transition-colors">
                  Simulate Normal Peak
                </h3>
                <p className="mt-1 text-xs text-zinc-400">
                  Generates healthy Saturday afternoon checkout volume across all categories.
                </p>
              </div>
              <div className="mt-4 flex items-center gap-1 text-[11px] font-medium text-emerald-400">
                <span>{isRunningScenario === "normal" ? "Injecting…" : "Generate peak"}</span>
                <ChevronRight className="h-3 w-3 group-hover:translate-x-1 transition-transform" />
              </div>
            </button>

            {/* Scenario 3: Reset Store State */}
            <button
              onClick={() =>
                handleInject(
                  "reset",
                  "Reset Store State",
                  "[STORE RESET] Catalog restored, test telemetry cleared, baseline anomalies restored."
                )
              }
              disabled={Boolean(isRunningScenario)}
              className="group relative flex flex-col justify-between rounded-xl border border-zinc-800 bg-gradient-to-b from-zinc-900 to-zinc-950 p-4 text-left transition-all hover:border-zinc-700 hover:shadow-lg"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 group-hover:scale-105 transition-transform">
                    <RefreshCw className="h-5 w-5" />
                  </div>
                  <span className="rounded bg-zinc-800 px-1.5 py-0.5 font-mono text-[10px] text-zinc-400">
                    BASELINE
                  </span>
                </div>
                <h3 className="font-semibold text-sm text-zinc-100 group-hover:text-cyan-300 transition-colors">
                  Reset Store State
                </h3>
                <p className="mt-1 text-xs text-zinc-400">
                  Wipes test mutations and restores initial baseline ledger stock across all 200 SKUs.
                </p>
              </div>
              <div className="mt-4 flex items-center gap-1 text-[11px] font-medium text-cyan-400">
                <span>{isRunningScenario === "reset" ? "Resetting…" : "Restore baseline"}</span>
                <ChevronRight className="h-3 w-3 group-hover:translate-x-1 transition-transform" />
              </div>
            </button>

            {/* Scenario 4: HERO BUTTON -> Run Scout Detection (F1) */}
            <button
              onClick={handleRunDetection}
              disabled={isDetecting}
              className="group relative flex flex-col justify-between rounded-xl border border-violet-500/50 bg-gradient-to-br from-violet-600 via-violet-700 to-scout-neon p-4 text-left text-white shadow-xl shadow-violet-950/50 transition-all hover:scale-[1.02] hover:shadow-2xl hover:shadow-violet-900/60 disabled:opacity-75"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/20 text-white backdrop-blur-sm group-hover:rotate-12 transition-transform">
                    <Sparkles className={`h-5 w-5 ${isDetecting ? "animate-spin" : ""}`} />
                  </div>
                  <span className="rounded bg-black/40 px-2 py-0.5 font-mono text-[10px] font-bold tracking-wider text-rose-200 uppercase">
                    Feature F1 ★
                  </span>
                </div>
                <h3 className="font-bold text-sm text-white">
                  Run Scout Detection &amp; Trigger Agent
                </h3>
                <p className="mt-1 text-xs text-violet-100/90 leading-relaxed">
                  Executes ZIP + Isolation Forest detector, recalibrates threshold, and creates floor checklist missions.
                </p>
              </div>
              <div className="mt-4 flex items-center gap-1.5 text-xs font-semibold text-white">
                <span>{isDetecting ? "Running detection…" : "Execute pipeline now"}</span>
                <PlayCircle className="h-3.5 w-3.5" />
              </div>
            </button>
          </div>
        </section>

        {/* Section 2: F1 Detection Outcome & Immediate Actions */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-scout-violet" />
              Detection Outcome &amp; Agent Dispatch (Feature F1)
            </h2>
            {detectionResult && (
              <span className="text-xs font-mono text-emerald-400">
                Status: {detectionResult.flagged} active voids flagged
              </span>
            )}
          </div>
          <DetectionOutcomeCard result={detectionResult} isRunning={isDetecting} />
        </section>

        {/* Section 3: F2 Live POS Terminal */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
              <Zap className="h-4 w-4 text-emerald-400" />
              Live POS Terminal Feed (Feature F2)
            </h2>
            <span className="text-xs text-zinc-500">
              Live checkout scanning stream with retail silence monitoring
            </span>
          </div>
          <PosTerminal scenarioNotice={scenarioNotice} />
        </section>

        {/* Section 4: Execution Log & Diagnostics */}
        <section className="rounded-xl border border-zinc-800 bg-zinc-950 p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
              Hub Execution Event Log
            </h3>
            <button
              onClick={() => setLog([])}
              className="text-[11px] text-zinc-500 hover:text-zinc-300"
            >
              Clear log
            </button>
          </div>
          <pre className="h-28 overflow-y-auto rounded-lg bg-black/80 p-3 font-mono text-[11px] text-emerald-400 scrollbar-thin scrollbar-thumb-zinc-800">
            {log.length > 0
              ? log.join("\n")
              : "[SYSTEM] Simulation hub ready. Click any trigger to induce scenarios or run detection."}
          </pre>
        </section>
      </div>
    </main>
  );
}
