"use client";
import { ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import type { Anomaly, AuditAction } from "@/lib/types";

interface ChecklistCardProps {
  item: Anomaly;
  onAction: (id: string, action: AuditAction) => void;
  onSelect?: (item: Anomaly) => void;
}

export function ChecklistCard({ item, onAction, onSelect }: ChecklistCardProps) {
  return (
    <div
      onClick={() => onSelect?.(item)}
      className="group relative cursor-pointer rounded-2xl border border-scout-border bg-scout-surface p-4 shadow-sm hover:border-zinc-400/60 hover:shadow-md transition-all active:scale-[0.99]"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <p className="font-semibold text-zinc-900 group-hover:text-zinc-950 transition">
              {item.sku_name}
            </p>
            {item.priority_level ? (
              <span
                className={`rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                  item.priority_level === "critical"
                    ? "bg-rose-500/15 text-rose-600 border border-rose-500/20"
                    : item.priority_level === "high"
                    ? "bg-amber-500/15 text-amber-600 border border-amber-500/20"
                    : item.priority_level === "medium"
                    ? "bg-blue-500/15 text-blue-600 border border-blue-500/20"
                    : "bg-zinc-100 text-zinc-600 border border-zinc-200"
                }`}
              >
                {item.priority_level}
              </span>
            ) : null}
            {item.revenue_at_risk && item.revenue_at_risk > 0 ? (
              <span className="rounded bg-rose-50 px-1.5 py-0.5 text-[10px] font-semibold text-rose-600 border border-rose-100">
                LKR {Math.round(item.revenue_at_risk).toLocaleString()} at risk
              </span>
            ) : null}
          </div>
          <p className="mt-0.5 text-xs text-scout-muted">
            Bay {item.bay} · Ledger <span className="font-medium text-zinc-800">{item.ledger_stock}</span> units ·{" "}
            <span className="font-medium text-amber-600">{item.hours_since_last_sale}h</span> silent
          </p>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          <Badge tone="alert">{Math.round(item.p_void * 100)}%</Badge>
          <ChevronRight className="h-4 w-4 text-zinc-400 group-hover:text-zinc-700 transition" />
        </div>
      </div>

      {item.why_flagged ? (
        <div className="mt-2.5 flex items-start gap-1.5 rounded-xl border border-purple-200/90 bg-purple-50/80 px-2.5 py-2 text-xs">
          <span className="text-xs shrink-0 select-none">💡</span>
          <p className="font-semibold text-zinc-950 leading-relaxed">
            {item.why_flagged}
          </p>
        </div>
      ) : null}

      {/* Direct Quick-Action Buttons */}
      <div className="mt-3.5 grid grid-cols-3 gap-2 pt-2 border-t border-scout-border/60">
        <Button
          variant="success"
          onClick={(e) => {
            e.stopPropagation();
            onAction(item.id, "restocked");
          }}
          className="py-2 text-xs font-semibold shadow-none hover:shadow"
        >
          Restocked
        </Button>
        <Button
          variant="warning"
          onClick={(e) => {
            e.stopPropagation();
            onAction(item.id, "damaged");
          }}
          className="py-2 text-xs font-semibold shadow-none hover:shadow"
        >
          Damaged
        </Button>
        <Button
          variant="ghost"
          onClick={(e) => {
            e.stopPropagation();
            onAction(item.id, "false_alarm");
          }}
          className="py-2 text-xs font-semibold border border-scout-border hover:bg-zinc-100"
        >
          False alarm
        </Button>
      </div>
    </div>
  );
}
