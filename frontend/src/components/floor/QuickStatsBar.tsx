"use client";
import { User, Clock, ShieldAlert } from "lucide-react";

interface QuickStatsBarProps {
  done: number;
  total: number;
  minutes: number;
  totalRevenueAtRisk?: number;
  associateName: string;
  onOpenAssociate: () => void;
}

export function QuickStatsBar({
  done,
  total,
  minutes,
  totalRevenueAtRisk,
  associateName,
  onOpenAssociate,
}: QuickStatsBarProps) {
  const pct = total === 0 ? 100 : Math.round((done / total) * 100);
  const remaining = Math.max(0, total - done);

  return (
    <div className="rounded-2xl border border-scout-border bg-scout-surface p-4 shadow-sm space-y-3">
      {/* Top Controls: Associate Identity & Session Status */}
      <div className="flex items-center justify-between pb-2.5 border-b border-scout-border/60">
        <button
          onClick={onOpenAssociate}
          className="flex items-center gap-1.5 rounded-full bg-zinc-100 hover:bg-zinc-200/80 px-2.5 py-1 text-xs font-semibold text-zinc-700 transition"
          title="Change Associate Name"
        >
          <User className="h-3.5 w-3.5 text-zinc-500" />
          <span>{associateName}</span>
          <span className="text-[10px] text-zinc-400 font-normal">(change)</span>
        </button>

        <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-zinc-500">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          Audit Session
        </span>
      </div>

      {/* Progress & Metrics */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs font-medium">
          <div className="flex items-center gap-1.5 text-zinc-800">
            <span className="font-bold text-sm text-zinc-950">{done}</span> of {total} verified
            {remaining > 0 ? (
              <span className="text-scout-muted flex items-center gap-0.5 ml-1">
                (<Clock className="h-3 w-3 inline" /> ~{minutes} min)
              </span>
            ) : null}
          </div>

          {totalRevenueAtRisk && totalRevenueAtRisk > 0 ? (
            <span className="flex items-center gap-1 rounded-full bg-rose-50 px-2 py-0.5 text-xs font-bold text-rose-600 border border-rose-100">
              <ShieldAlert className="h-3.5 w-3.5" />
              LKR {Math.round(totalRevenueAtRisk).toLocaleString()}
            </span>
          ) : null}
        </div>

        {/* Animated Progress Bar */}
        <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-zinc-100">
          <div
            className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 shadow-sm transition-all duration-300 ease-out"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    </div>
  );
}
