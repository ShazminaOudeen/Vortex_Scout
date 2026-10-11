"use client";

import Link from "next/link";
import {
  AlertOctagon,
  ArrowRight,
  CheckCircle2,
  ClipboardList,
  LayoutDashboard,
  Boxes,
  Sparkles,
  ShieldCheck,
  ChevronRight,
} from "lucide-react";
import type { DetectionRunResult } from "@/lib/types";

interface DetectionOutcomeCardProps {
  result: DetectionRunResult | null;
  isRunning: boolean;
}

export function DetectionOutcomeCard({ result, isRunning }: DetectionOutcomeCardProps) {
  if (isRunning) {
    return (
      <div className="rounded-xl border border-violet-500/30 bg-zinc-950/80 p-8 shadow-xl backdrop-blur-md animate-pulse">
        <div className="flex flex-col items-center justify-center text-center">
          <div className="relative mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-violet-900/30 text-violet-400 border border-violet-500/50">
            <Sparkles className="h-7 w-7 animate-spin text-scout-violet" />
          </div>
          <h3 className="text-lg font-bold text-zinc-100">
            Executing Vortex Scout Detection Engine…
          </h3>
          <p className="mt-1 max-w-md text-sm text-zinc-400">
            Scanning feature store velocity buckets, calibrating adaptive void threshold,
            and triggering the Gemini floor checklist agent…
          </p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-6 text-center text-zinc-400">
        <p className="text-sm">
          No detection cycle executed yet. Click{" "}
          <strong className="text-scout-neon">Run Scout Detection &amp; Trigger Agent</strong>{" "}
          above to execute the detection pipeline and generate floor missions.
        </p>
      </div>
    );
  }

  const hasAlerts = result.flagged > 0;

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/90 shadow-2xl backdrop-blur-md overflow-hidden">
      {/* Top Banner */}
      <div
        className={`px-6 py-4 border-b flex flex-wrap items-center justify-between gap-4 ${
          hasAlerts
            ? "bg-rose-950/40 border-rose-500/30"
            : "bg-emerald-950/30 border-emerald-500/30"
        }`}
      >
        <div className="flex items-center gap-3">
          <div
            className={`flex h-10 w-10 items-center justify-center rounded-xl border ${
              hasAlerts
                ? "bg-rose-900/40 border-rose-500/50 text-rose-400"
                : "bg-emerald-900/40 border-emerald-500/50 text-emerald-400"
            }`}
          >
            {hasAlerts ? (
              <AlertOctagon className="h-5 w-5" />
            ) : (
              <CheckCircle2 className="h-5 w-5" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-zinc-100">
                {hasAlerts
                  ? `Detection Complete — ${result.flagged} Shelf Void${result.flagged > 1 ? "s" : ""} Flagged`
                  : "Detection Complete — All Shelves Healthy"}
              </h3>
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                  hasAlerts
                    ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                    : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                }`}
              >
                {hasAlerts ? "ANOMALIES ACTIVE" : "ALL CLEAR"}
              </span>
            </div>
            <p className="text-xs text-zinc-400">
              Calibrated Threshold:{" "}
              <strong className="text-zinc-200">
                {(result.threshold * 100).toFixed(0)}%
              </strong>{" "}
              · Created:{" "}
              <strong className="text-zinc-200">{result.created}</strong> ·
              Updated:{" "}
              <strong className="text-zinc-200">{result.updated}</strong> ·
              Cleared:{" "}
              <strong className="text-zinc-200">{result.cleared}</strong>
              {result.data_as_of && (
                <> · Data as of: {result.data_as_of.replace("T", " ")}</>
              )}
            </p>
          </div>
        </div>

        {/* Calibration Badge */}
        {result.calibration && (
          <div className="flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-900/80 px-3 py-1.5 text-xs text-zinc-300">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span>
              Adaptive Threshold:{" "}
              <strong className="text-emerald-300">
                {(result.calibration.effective_threshold * 100).toFixed(0)}%
              </strong>
            </span>
          </div>
        )}
      </div>

      {/* Action Links Bar (Crucial for F1 demo flow!) */}
      <div className="border-b border-zinc-800 bg-zinc-900/50 p-4">
        <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-400">
          Immediate Resolution &amp; Inspection Links
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Action 1: Floor Checklist */}
          <Link
            href="/floor"
            className="group relative flex items-center justify-between rounded-xl border border-violet-500/30 bg-gradient-to-r from-violet-950/50 to-zinc-900 p-4 transition-all hover:border-violet-500/60 hover:shadow-lg hover:shadow-violet-900/20"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-scout-violet/20 text-scout-violet border border-violet-500/30 group-hover:scale-105 transition-transform">
                <ClipboardList className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-sm text-zinc-100 group-hover:text-violet-300 transition-colors">
                    Floor Checklist
                  </span>
                  {hasAlerts && (
                    <span className="rounded-full bg-rose-500/20 px-2 py-0.5 text-[10px] font-bold text-rose-300">
                      {result.flagged} Tasks
                    </span>
                  )}
                </div>
                <p className="text-xs text-zinc-400">
                  Send floor staff to audit Aisle &amp; Bay
                </p>
              </div>
            </div>
            <ArrowRight className="h-4 w-4 text-zinc-500 group-hover:text-violet-400 group-hover:translate-x-1 transition-all" />
          </Link>

          {/* Action 2: Manager Portal */}
          <Link
            href="/dashboard"
            className="group relative flex items-center justify-between rounded-xl border border-zinc-800 bg-gradient-to-r from-zinc-900 to-zinc-900/80 p-4 transition-all hover:border-zinc-700 hover:shadow-lg"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 group-hover:scale-105 transition-transform">
                <LayoutDashboard className="h-5 w-5" />
              </div>
              <div>
                <span className="font-semibold text-sm text-zinc-100 group-hover:text-emerald-300 transition-colors">
                  Store Manager Portal
                </span>
                <p className="text-xs text-zinc-400">
                  Inspect real-time revenue &amp; velocity
                </p>
              </div>
            </div>
            <ArrowRight className="h-4 w-4 text-zinc-500 group-hover:text-emerald-400 group-hover:translate-x-1 transition-all" />
          </Link>

          {/* Action 3: Full Inventory */}
          <Link
            href="/inventory"
            className="group relative flex items-center justify-between rounded-xl border border-zinc-800 bg-gradient-to-r from-zinc-900 to-zinc-900/80 p-4 transition-all hover:border-zinc-700 hover:shadow-lg"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 group-hover:scale-105 transition-transform">
                <Boxes className="h-5 w-5" />
              </div>
              <div>
                <span className="font-semibold text-sm text-zinc-100 group-hover:text-cyan-300 transition-colors">
                  Inventory Explorer
                </span>
                <p className="text-xs text-zinc-400">
                  Search all 200 SKUs &amp; ledger stock
                </p>
              </div>
            </div>
            <ArrowRight className="h-4 w-4 text-zinc-500 group-hover:text-cyan-400 group-hover:translate-x-1 transition-all" />
          </Link>
        </div>
      </div>

      {/* Flagged Alerts Breakdown Cards */}
      {hasAlerts && result.alerts && result.alerts.length > 0 && (
        <div className="p-5">
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-400">
            Detected Shelf-Void Alerts ({result.alerts.length})
          </h4>
          <div className="space-y-3">
            {result.alerts.map((alert) => (
              <div
                key={alert.sku_id}
                className="rounded-xl border border-rose-500/20 bg-zinc-900/60 p-4 hover:border-rose-500/40 transition-colors"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  {/* SKU Info */}
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-xs font-bold text-violet-400">
                        {alert.sku_id}
                      </span>
                      <span className="text-sm font-semibold text-zinc-100">
                        {alert.sku_name}
                      </span>
                      <span className="rounded bg-zinc-800 px-2 py-0.5 text-[11px] text-zinc-300">
                        {alert.category}
                      </span>
                      <span className="rounded bg-violet-950/70 border border-violet-500/30 px-2 py-0.5 text-[11px] font-medium text-violet-300">
                        Aisle {alert.aisle} · Bay {alert.bay}
                      </span>
                    </div>

                    {/* Narrative Explanation */}
                    <p className="mt-2 text-xs text-zinc-300 italic bg-black/40 rounded p-2 border border-zinc-800">
                      &ldquo;{alert.why_flagged}&rdquo;
                    </p>
                  </div>

                  {/* Metrics Badges */}
                  <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
                    {/* P(Void) Score */}
                    <div className="rounded-lg border border-rose-500/40 bg-rose-950/60 px-3 py-1 text-right">
                      <div className="text-[10px] text-rose-300">VOID PROB</div>
                      <div className="text-sm font-bold text-rose-400">
                        {(alert.p_void * 100).toFixed(0)}%
                      </div>
                    </div>

                    {/* Revenue At Risk */}
                    <div className="rounded-lg border border-amber-500/30 bg-amber-950/40 px-3 py-1 text-right">
                      <div className="text-[10px] text-amber-300">REV AT RISK</div>
                      <div className="text-sm font-bold text-amber-400">
                        LKR {alert.revenue_at_risk?.toLocaleString() || "—"}
                      </div>
                    </div>

                    {/* Silent Hours */}
                    <div className="rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-1 text-right">
                      <div className="text-[10px] text-zinc-400">SILENT TIME</div>
                      <div className="text-sm font-bold text-zinc-200">
                        {alert.silent_hours}h
                      </div>
                    </div>
                  </div>
                </div>

                {/* Bottom link to view SKU in inventory or resolve */}
                <div className="mt-3 flex items-center justify-between border-t border-zinc-800/80 pt-2 text-xs">
                  <div className="flex items-center gap-3 text-zinc-400">
                    <span>
                      Ledger Stock:{" "}
                      <strong className="text-zinc-200">
                        {alert.ledger_stock} units
                      </strong>
                    </span>
                    <span>·</span>
                    <span>
                      Expected Sales:{" "}
                      <strong className="text-zinc-200">
                        ~{alert.expected_sales} units
                      </strong>
                    </span>
                    {alert.suggested_action && (
                      <>
                        <span>·</span>
                        <span className="capitalize text-emerald-400">
                          Suggested: {alert.suggested_action}
                        </span>
                      </>
                    )}
                  </div>
                  <Link
                    href={`/inventory/${alert.sku_id}`}
                    className="flex items-center gap-1 text-violet-400 hover:text-violet-300 font-medium"
                  >
                    <span>Inspect SKU Details</span>
                    <ChevronRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
