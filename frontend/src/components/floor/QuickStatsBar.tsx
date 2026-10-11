export function QuickStatsBar({
  done,
  total,
  minutes,
  totalRevenueAtRisk,
}: {
  done: number;
  total: number;
  minutes: number;
  totalRevenueAtRisk?: number;
}) {
  const pct = total === 0 ? 100 : Math.round((done / total) * 100);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm font-medium">
        <p>
          {done} of {total} items verified ({minutes} min remaining)
        </p>
        {totalRevenueAtRisk && totalRevenueAtRisk > 0 ? (
          <span className="text-xs font-semibold text-rose-500">
            LKR {Math.round(totalRevenueAtRisk).toLocaleString()} at risk
          </span>
        ) : null}
      </div>
      <div className="h-2 w-full rounded-full bg-zinc-200">
        <div className="h-2 rounded-full bg-scout-success transition-all" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
