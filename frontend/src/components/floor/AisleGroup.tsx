import type { AuditAction, ChecklistGroup } from "@/lib/types";
import { ChecklistCard } from "./ChecklistCard";

export function AisleGroup({
  group,
  onAction,
}: {
  group: ChecklistGroup;
  onAction: (id: string, action: AuditAction) => void;
}) {
  return (
    <section className="space-y-2">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-scout-muted">{group.title}</h2>
      {group.items.map((item) => (
        <ChecklistCard key={item.id} item={item} onAction={onAction} />
      ))}
    </section>
  );
}
