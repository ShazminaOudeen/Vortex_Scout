"use client";
import { useEffect, useState } from "react";
import { RotateCcw, Check, AlertTriangle, HelpCircle } from "lucide-react";
import type { AuditAction } from "@/lib/types";

interface UndoToastProps {
  skuName: string;
  action: AuditAction;
  onUndo: () => void;
  onDismiss: () => void;
  durationMs?: number;
}

export function UndoToast({
  skuName,
  action,
  onUndo,
  onDismiss,
  durationMs = 8000,
}: UndoToastProps) {
  const [progress, setProgress] = useState(100);

  useEffect(() => {
    const startTime = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 100 - (elapsed / durationMs) * 100);
      setProgress(remaining);
      if (remaining <= 0) {
        clearInterval(interval);
        onDismiss();
      }
    }, 50);

    return () => clearInterval(interval);
  }, [durationMs, onDismiss]);

  const actionLabels: Record<AuditAction, { label: string; icon: typeof Check; color: string }> = {
    restocked: { label: "Restocked", icon: Check, color: "text-emerald-400" },
    damaged: { label: "Damaged write-off", icon: AlertTriangle, color: "text-amber-400" },
    false_alarm: { label: "False alarm", icon: HelpCircle, color: "text-blue-400" },
  };

  const actionInfo = actionLabels[action] || actionLabels.restocked;
  const ActionIcon = actionInfo.icon;

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-full max-w-[390px] px-4 animate-in slide-in-from-bottom-5 duration-200">
      <div className="relative overflow-hidden rounded-2xl border border-zinc-700 bg-zinc-900/95 p-3.5 shadow-2xl backdrop-blur-md text-white">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-zinc-800">
              <ActionIcon className={`h-4 w-4 ${actionInfo.color}`} />
            </div>
            <div className="overflow-hidden">
              <p className="truncate text-xs font-medium text-zinc-200">{skuName}</p>
              <p className="text-[11px] text-zinc-400">{actionInfo.label}</p>
            </div>
          </div>

          <button
            onClick={onUndo}
            className="flex items-center gap-1.5 rounded-xl bg-white px-3 py-1.5 text-xs font-bold text-zinc-900 hover:bg-zinc-200 active:scale-95 transition"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Undo
          </button>
        </div>

        {/* Progress bar countdown */}
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-zinc-800">
          <div
            className="h-full bg-emerald-500 transition-all duration-75"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  );
}
