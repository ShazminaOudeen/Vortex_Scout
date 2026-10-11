"use client";
import type { Anomaly, AuditAction, ChecklistGroup } from "@/lib/types";
import { ChecklistCard } from "./ChecklistCard";

export function AisleGroup({
  group,
  onAction,
  onSelect,
}: {
  group: ChecklistGroup;
  onAction: (id: string, action: AuditAction) => void;
  onSelect?: (item: Anomaly) => void;
}) {
  if (group.items.length === 0) return null;

  return (
    <section className="space-y-2.5">
      <div className="flex items-center justify-between px-1">
        <h2 className="text-xs font-bold uppercase tracking-wider text-scout-muted">
          {group.title}
        </h2>
        <span className="rounded-full bg-zinc-200/70 px-2 py-0.5 text-[10px] font-bold text-zinc-600">
          {group.items.length} {group.items.length === 1 ? "item" : "items"}
        </span>
      </div>
      <div className="space-y-2.5">
        {group.items.map((item) => (
          <ChecklistCard
            key={item.id}
            item={item}
            onAction={onAction}
            onSelect={onSelect}
          />
        ))}
      </div>
    </section>
  );
}
