"use client";
import { useEffect, useState, useRef } from "react";
import { RotateCcw, CheckCircle2, AlertTriangle, ShieldCheck, X } from "lucide-react";
import type { Anomaly, AuditAction } from "@/lib/types";

interface UndoToastProps {
  skuName: string;
  action: AuditAction;
  anomaly?: Anomaly;
  onUndo: () => void;
  onDismiss: () => void;
  durationMs?: number;
}

interface ActionConfig {
  title: string;
  icon: typeof CheckCircle2;
  iconColor: string;
  iconBg: string;
  cardBorder: string;
  cardBg: string;
  cardShadow: string;
  titleColor: string;
  progressBarColor: string;
  trackBg: string;
  getMessage: (anomaly?: Anomaly) => string;
}

const ACTION_CONFIGS: Record<AuditAction, ActionConfig> = {
  restocked: {
    title: "Restocked",
    icon: CheckCircle2,
    iconColor: "text-emerald-700",
    iconBg: "bg-emerald-100",
    cardBorder: "border-emerald-300",
    cardBg: "bg-white",
    cardShadow: "shadow-2xl shadow-emerald-950/15",
    titleColor: "text-emerald-700",
    progressBarColor: "bg-emerald-500",
    trackBg: "bg-emerald-100",
    getMessage: (anomaly) => {
      const bay = anomaly?.bay ? `Bay ${anomaly.bay} shelf facing replenished.` : "Shelf facing replenished.";
      const amount = anomaly?.revenue_at_risk
        ? ` LKR ${Math.round(anomaly.revenue_at_risk).toLocaleString()} revenue protected.`
        : " Availability restored.";
      return `${bay}${amount}`;
    },
  },
  damaged: {
    title: "Damaged Write-Off",
    icon: AlertTriangle,
    iconColor: "text-amber-700",
    iconBg: "bg-amber-100",
    cardBorder: "border-amber-300",
    cardBg: "bg-white",
    cardShadow: "shadow-2xl shadow-amber-950/15",
    titleColor: "text-amber-700",
    progressBarColor: "bg-amber-500",
    trackBg: "bg-amber-100",
    getMessage: (anomaly) => {
      const bay = anomaly?.bay ? `Damaged units removed from Bay ${anomaly.bay}.` : "Damaged units removed.";
      const amount = anomaly?.revenue_at_risk
        ? ` LKR ${Math.round(anomaly.revenue_at_risk).toLocaleString()} recorded in waste ledger.`
        : " Inventory ledger adjusted.";
      return `${bay}${amount}`;
    },
  },
  false_alarm: {
    title: "False Alarm",
    icon: ShieldCheck,
    iconColor: "text-blue-700",
    iconBg: "bg-blue-100",
    cardBorder: "border-blue-300",
    cardBg: "bg-white",
    cardShadow: "shadow-2xl shadow-blue-950/15",
    titleColor: "text-blue-700",
    progressBarColor: "bg-blue-500",
    trackBg: "bg-blue-100",
    getMessage: (anomaly) => {
      const bay = anomaly?.bay ? `Stock confirmed present at Bay ${anomaly.bay}.` : "Physical stock confirmed on shelf.";
      const amount = anomaly?.revenue_at_risk
        ? ` LKR ${Math.round(anomaly.revenue_at_risk).toLocaleString()} void alert dismissed.`
        : " Void alert cleared.";
      return `${bay}${amount}`;
    },
  },
};

export function UndoToast({
  skuName,
  action,
  anomaly,
  onUndo,
  onDismiss,
  durationMs = 12000,
}: UndoToastProps) {
  const [progress, setProgress] = useState(100);
  const [isPaused, setIsPaused] = useState(false);
  const remainingTimeRef = useRef(durationMs);
  const lastTickRef = useRef(Date.now());

  useEffect(() => {
    lastTickRef.current = Date.now();

    const interval = setInterval(() => {
      const now = Date.now();
      const delta = now - lastTickRef.current;
      lastTickRef.current = now;

      if (!isPaused) {
        remainingTimeRef.current = Math.max(0, remainingTimeRef.current - delta);
        const nextProgress = (remainingTimeRef.current / durationMs) * 100;
        setProgress(nextProgress);

        if (remainingTimeRef.current <= 0) {
          clearInterval(interval);
          onDismiss();
        }
      }
    }, 40);

    return () => clearInterval(interval);
  }, [durationMs, onDismiss, isPaused]);

  const config = ACTION_CONFIGS[action] || ACTION_CONFIGS.restocked;
  const ActionIcon = config.icon;
  const message = config.getMessage(anomaly);

  return (
    <div
      className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-full max-w-[440px] px-4 animate-in slide-in-from-bottom-5 fade-in duration-300"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => {
        lastTickRef.current = Date.now();
        setIsPaused(false);
      }}
      onTouchStart={() => setIsPaused(true)}
      onTouchEnd={() => {
        lastTickRef.current = Date.now();
        setIsPaused(false);
      }}
    >
      <div
        className={`relative overflow-hidden rounded-2xl border ${config.cardBorder} ${config.cardBg} ${config.cardShadow} p-3.5 space-y-2`}
      >
        {/* Row 1: Action Status + SKU + Amount + Buttons */}
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl ${config.iconBg}`}>
              <ActionIcon className={`h-4.5 w-4.5 ${config.iconColor}`} />
            </div>

            <div className="min-w-0 flex items-center gap-1.5 flex-wrap">
              <span className={`text-xs font-extrabold uppercase tracking-wider ${config.titleColor}`}>
                {config.title}
              </span>
              <span className="text-zinc-300">·</span>
              <span className="truncate text-xs font-bold text-zinc-950 max-w-[150px]" title={skuName}>
                {skuName}
              </span>
              {anomaly?.revenue_at_risk && anomaly.revenue_at_risk > 0 ? (
                <span
                  className={`rounded-md px-1.5 py-0.5 text-[10px] font-extrabold border ${
                    action === "restocked"
                      ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                      : action === "damaged"
                      ? "bg-amber-50 text-amber-800 border-amber-200"
                      : "bg-blue-50 text-blue-800 border-blue-200"
                  }`}
                >
                  LKR {Math.round(anomaly.revenue_at_risk).toLocaleString()}
                </span>
              ) : null}
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-1.5 shrink-0">
            <button
              onClick={onUndo}
              className="flex items-center gap-1 rounded-xl bg-zinc-900 hover:bg-zinc-800 px-2.5 py-1 text-xs font-bold text-white shadow-sm active:scale-95 transition"
              title="Undo this action"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Undo</span>
            </button>

            <button
              onClick={onDismiss}
              className="rounded-lg p-1 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700 transition"
              title="Dismiss notification"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* Row 2: Clean Confirmation Message with proper indent */}
        <div className="pl-[42px]">
          <p className="text-xs text-zinc-600 font-medium leading-relaxed">
            {message}
          </p>
        </div>

        {/* Progress bar countdown */}
        <div className={`absolute bottom-0 left-0 right-0 h-1.5 ${config.trackBg}`}>
          <div
            className={`h-full ${config.progressBarColor} transition-all duration-75`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  );
}
