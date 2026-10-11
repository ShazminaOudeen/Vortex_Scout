"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface CategoryRiskChartProps {
  data: { category: string; share: number }[];
}

export function CategoryRiskChart({ data }: CategoryRiskChartProps) {
  const hasData = data && data.length > 0;

  return (
    <div className="rounded-xl border border-scout-border bg-scout-surface p-5">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-zinc-900">
          Phantom Stock Risk by Category
        </h3>
        <p className="text-xs text-scout-muted">
          Distribution of active shelf-void anomalies across supermarket categories.
        </p>
      </div>

      <div className="h-64 w-full">
        {!hasData ? (
          <div className="flex h-full flex-col items-center justify-center rounded-lg border border-dashed border-zinc-200 p-6 text-center text-sm text-scout-muted">
            <p className="font-medium text-zinc-700">No active category anomalies</p>
            <p className="mt-1 text-xs">
              All categories currently have healthy on-shelf availability.
            </p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              margin={{ top: 10, right: 20, left: -10, bottom: 25 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#F4F4F5" />
              <XAxis
                dataKey="category"
                tick={{ fontSize: 11, fill: "#71717A" }}
                interval={0}
                angle={-15}
                textAnchor="end"
              />
              <YAxis
                unit="%"
                tick={{ fontSize: 11, fill: "#71717A" }}
                domain={[0, 100]}
              />
              <Tooltip
                formatter={(val) => [`${val}%`, "Share of voids"]}
                contentStyle={{
                  backgroundColor: "#FFFFFF",
                  borderColor: "#E4E4E7",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
              />
              <Bar
                dataKey="share"
                fill="#8B5CF6"
                radius={[4, 4, 0, 0]}
                name="Share of Voids (%)"
              />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
