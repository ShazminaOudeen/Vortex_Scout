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
          <p className="font-semibold">{item.sku_name}</p>
          <p className="text-xs text-scout-muted">
            Bay {item.bay} · Ledger {item.ledger_stock} units · {item.hours_since_last_sale}h since last sale
          </p>
        </div>
        <Badge tone="alert">{Math.round(item.p_void * 100)}%</Badge>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-2">
        <Button variant="success" onClick={() => onAction(item.id, "restocked")}>Restocked</Button>
        <Button variant="warning" onClick={() => onAction(item.id, "damaged")}>Damaged</Button>
        <Button variant="ghost" onClick={() => onAction(item.id, "false_alarm")}>False alarm</Button>
      </div>
    </div>
  );
}
