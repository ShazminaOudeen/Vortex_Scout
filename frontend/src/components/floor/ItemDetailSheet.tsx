"use client";
import { X, Sparkles } from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";
import { Button } from "@/components/ui/Button";
import { useVelocity } from "@/hooks/useAnomalies";
import type { Anomaly, AuditAction } from "@/lib/types";

interface ItemDetailSheetProps {
  item: Anomaly | null;
  onClose: () => void;
  onAction: (id: string, action: AuditAction) => void;
}

export function ItemDetailSheet({ item, onClose, onAction }: ItemDetailSheetProps) {
  const { data: velocityData } = useVelocity(
    item ? { anomalyId: item.id, skuId: item.sku_id } : undefined
  );

  if (!item) return null;

  const points = velocityData?.points && velocityData.points.length > 0
    ? velocityData.points
    : [
        { hour: "-6h", expected: 3.8, actual: 4 },
        { hour: "-5h", expected: 4.1, actual: 3 },
        { hour: "-4h", expected: 3.5, actual: 4 },
        { hour: "-3h", expected: 4.2, actual: 0 },
        { hour: "-2h", expected: 4.5, actual: 0 },
        { hour: "-1h", expected: 3.9, actual: 0 },
        { hour: "Now", expected: 4.0, actual: 0 },
      ];

  const handleAction = (action: AuditAction) => {
    onAction(item.id, action);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 backdrop-blur-sm p-0 sm:p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-lg rounded-t-3xl sm:rounded-2xl border border-scout-border bg-scout-surface p-5 shadow-2xl max-h-[90vh] overflow-y-auto animate-in slide-in-from-bottom-8 sm:zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 pb-3 border-b border-scout-border">
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded bg-zinc-100 px-2 py-0.5 text-[11px] font-mono font-semibold text-zinc-600">
                Aisle {item.aisle} · Bay {item.bay}
              </span>
              <span className="rounded bg-rose-500/10 px-2 py-0.5 text-[11px] font-semibold text-rose-500 uppercase">
                {item.priority_level || "high"} priority
              </span>
            </div>
            <h2 className="mt-1.5 text-lg font-bold text-zinc-900 leading-snug">
              {item.sku_name}
            </h2>
            <p className="text-xs text-scout-muted">{item.category}</p>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-1.5 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Quick Metrics Bar */}
        <div className="mt-4 grid grid-cols-4 gap-2 text-center">
          <div className="rounded-xl border border-scout-border bg-scout-bg p-2.5">
            <p className="text-[10px] uppercase font-bold text-scout-muted">p(void)</p>
            <p className="text-base font-extrabold text-rose-600">
              {Math.round(item.p_void * 100)}%
            </p>
          </div>
          <div className="rounded-xl border border-scout-border bg-scout-bg p-2.5">
            <p className="text-[10px] uppercase font-bold text-scout-muted">Ledger</p>
            <p className="text-base font-extrabold text-zinc-900">
              {item.ledger_stock} <span className="text-[10px] font-normal">units</span>
            </p>
          </div>
          <div className="rounded-xl border border-scout-border bg-scout-bg p-2.5">
            <p className="text-[10px] uppercase font-bold text-scout-muted">Silent</p>
            <p className="text-base font-extrabold text-amber-600">
              {item.hours_since_last_sale}h
            </p>
          </div>
          <div className="rounded-xl border border-scout-border bg-scout-bg p-2.5">
            <p className="text-[10px] uppercase font-bold text-scout-muted">At Risk</p>
            <p className="text-base font-extrabold text-zinc-900">
              LKR {Math.round(item.revenue_at_risk || 0).toLocaleString()}
            </p>
          </div>
        </div>

        {/* Gemini AI Reason Card (Feature C3 / D4) */}
        <div className="mt-4 rounded-xl border border-purple-200/90 bg-purple-50/80 p-3.5 shadow-sm">
          <div className="flex items-center gap-1.5 text-xs font-bold text-purple-900">
            <Sparkles className="h-4 w-4 text-purple-700" />
            <span>Scout AI Diagnostic & Root Cause</span>
          </div>
          <p className="mt-2 text-xs font-semibold text-zinc-950 leading-relaxed">
            {item.why_flagged ||
              `Expected steady sales based on store rhythm. Zero transactions recorded in ${item.hours_since_last_sale} consecutive trading hours while ledger lists ${item.ledger_stock} units. Shelf is likely voided due to backroom misplacement or damaged write-off lag.`}
          </p>
          {item.suggested_action && (
            <div className="mt-2.5 flex items-center justify-between pt-2 border-t border-purple-200">
              <span className="text-xs font-bold text-purple-900">
                Recommended action:
              </span>
              <span className="rounded-md bg-purple-700 px-2.5 py-0.5 text-xs font-bold uppercase tracking-wider text-white shadow-sm">
                {item.suggested_action.replace("_", " ")}
              </span>
            </div>
          )}
        </div>

        {/* Mini Sales Velocity Curve (Expected vs Actual) */}
        <div className="mt-4 rounded-xl border border-scout-border bg-scout-bg p-3.5">
          <div className="flex items-center justify-between mb-2">
            <div>
              <p className="text-xs font-semibold text-zinc-900">Hourly Sales Velocity</p>
              <p className="text-[11px] text-scout-muted">
                Notice actual sales drop to zero while expected pace continued
              </p>
            </div>
            <div className="flex items-center gap-3 text-[11px]">
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-indigo-500" />
                <span className="text-zinc-600">Expected</span>
              </span>
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-rose-500" />
                <span className="text-zinc-600">Actual</span>
              </span>
            </div>
          </div>

          <div className="h-32 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={points} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorExpected" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#818CF8" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#818CF8" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#F43F5E" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#F43F5E" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="hour" tick={{ fontSize: 10 }} tickLine={false} />
                <YAxis tick={{ fontSize: 10 }} tickLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#18181B",
                    borderColor: "#27272A",
                    borderRadius: "8px",
                    color: "#FAFAFA",
                    fontSize: "11px",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="expected"
                  stroke="#6366F1"
                  strokeWidth={2}
                  strokeDasharray="4 2"
                  fill="url(#colorExpected)"
                  name="Expected /hr"
                />
                <Area
                  type="monotone"
                  dataKey="actual"
                  stroke="#E11D48"
                  strokeWidth={2.5}
                  fill="url(#colorActual)"
                  name="Actual sold"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-scout-muted mb-2">
            Reconcile Shelf State
          </p>
          <div className="grid grid-cols-3 gap-2.5">
            <Button
              variant="success"
              onClick={() => handleAction("restocked")}
              className="py-3 font-semibold text-xs flex flex-col items-center gap-1 shadow-sm"
            >
              <span>Restocked</span>
              <span className="text-[10px] font-normal opacity-90">Stocked shelf</span>
            </Button>
            <Button
              variant="warning"
              onClick={() => handleAction("damaged")}
              className="py-3 font-semibold text-xs flex flex-col items-center gap-1 shadow-sm"
            >
              <span>Damaged</span>
              <span className="text-[10px] font-normal opacity-90">Write off units</span>
            </Button>
            <Button
              variant="ghost"
              onClick={() => handleAction("false_alarm")}
              className="py-3 font-semibold text-xs flex flex-col items-center gap-1 border border-scout-border"
            >
              <span>False Alarm</span>
              <span className="text-[10px] font-normal opacity-90">Item on shelf</span>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
