"use client";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import type { Anomaly, AuditAction } from "@/lib/types";

// TODO(Task 3): wire onAction to api.reconcile + haptic/audio feedback.
export function ChecklistCard({
  item,
  onAction,
}: {
  item: Anomaly;
  onAction: (id: string, action: AuditAction) => void;
}) {
  return (
    <div className="rounded-xl border border-scout-border bg-scout-surface p-4 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="flex flex-wrap items-center gap-1.5">
            <p className="font-semibold">{item.sku_name}</p>
            {item.revenue_at_risk && item.revenue_at_risk > 0 ? (
              <span className="rounded bg-rose-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-rose-400">
                LKR {Math.round(item.revenue_at_risk).toLocaleString()} at risk
              </span>
            ) : null}
          </div>
          <p className="text-xs text-scout-muted">
            Bay {item.bay} · Ledger {item.ledger_stock} units · {item.hours_since_last_sale}h since last sale
          </p>
        </div>
        <Badge tone="alert">{Math.round(item.p_void * 100)}%</Badge>
      </div>
      {item.why_flagged ? (
        <p className="mt-2.5 rounded-lg border border-zinc-800/80 bg-zinc-900/60 px-2.5 py-1.5 text-xs italic text-zinc-300">
          💡 {item.why_flagged}
        </p>
      ) : null}
      <div className="mt-3 grid grid-cols-3 gap-2">
        <Button variant="success" onClick={() => onAction(item.id, "restocked")}>Restocked</Button>
        <Button variant="warning" onClick={() => onAction(item.id, "damaged")}>Damaged</Button>
        <Button variant="ghost" onClick={() => onAction(item.id, "false_alarm")}>False alarm</Button>
      </div>
    </div>
  );
}
