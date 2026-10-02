export function QuickStatsBar({ done, total, minutes }: { done: number; total: number; minutes: number }) {
  const pct = total === 0 ? 100 : Math.round((done / total) * 100);
  return (
    <div className="space-y-1">
      <p className="text-sm font-medium">
        {done} of {total} items verified ({minutes} min remaining)
      </p>
      <div className="h-2 w-full rounded-full bg-zinc-200">
        <div className="h-2 rounded-full bg-scout-success transition-all" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
