"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useVelocity } from "@/hooks/useAnomalies";
import type { VelocityPoint } from "@/lib/types";

interface VelocityChartProps {
  anomalyId?: string;
  skuId?: string;
  data?: VelocityPoint[];
  title?: string;
  subtitle?: string;
}

export function VelocityChart({
  anomalyId,
  skuId,
  data: directData,
  title = "Sales Velocity: Expected vs. Actual (Last 24 Open Hours)",
  subtitle,
}: VelocityChartProps) {
  const { data: fetched, isLoading } = useVelocity(
    !directData ? { anomalyId, skuId } : undefined
  );

  const points = directData ?? fetched?.points ?? [];
  const hasData = directData ? directData.length > 0 : Boolean(fetched?.has_data && points.length > 0);
  const skuName = fetched?.sku_name;

  return (
    <div className="rounded-xl border border-scout-border bg-scout-surface p-5">
      <div className="mb-4 flex flex-col justify-between gap-1 sm:flex-row sm:items-center">
        <div>
          <h3 className="text-base font-semibold text-zinc-900">{title}</h3>
          <p className="text-xs text-scout-muted">
            {subtitle ??
              (skuName
                ? `Inspecting product: ${skuName}`
                : "Expected curve derived from store hourly rhythm; actual drops to 0 during shelf voids.")}
          </p>
        </div>
        {hasData && (
          <div className="flex items-center gap-4 text-xs font-medium">
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-[#7C3AED]" />
              Expected sales
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-[#E11D48]" />
              Actual POS sales
            </span>
          </div>
        )}
      </div>

      <div className="h-72 w-full">
        {isLoading ? (
          <div className="flex h-full items-center justify-center text-sm text-scout-muted">
            Loading sales velocity data...
          </div>
        ) : !hasData ? (
          <div className="flex h-full flex-col items-center justify-center rounded-lg border border-dashed border-zinc-200 p-6 text-center text-sm text-scout-muted">
            <p className="font-medium text-zinc-700">No POS transactions recorded yet for this item</p>
            <p className="mt-1 text-xs">
              Expected-vs-actual curves reflect real transaction history. Stream POS data or simulate trading to populate the feature store.
            </p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={points} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F4F4F5" />
              <XAxis dataKey="hour" tick={{ fontSize: 11, fill: "#71717A" }} />
              <YAxis tick={{ fontSize: 11, fill: "#71717A" }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#FFFFFF",
                  borderColor: "#E4E4E7",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
              />
              <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }} />
              <Line
                type="monotone"
                dataKey="expected"
                name="Expected (units/hr)"
                stroke="#7C3AED"
                strokeWidth={2}
                dot={{ r: 2 }}
                activeDot={{ r: 5 }}
              />
              <Line
                type="monotone"
                dataKey="actual"
                name="Actual (units/hr)"
                stroke="#E11D48"
                strokeWidth={2}
                dot={{ r: 2 }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
