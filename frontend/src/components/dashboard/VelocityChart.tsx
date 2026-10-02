"use client";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

// TODO(Task 3): feed with real expected-vs-actual velocity from the API.
const placeholder = Array.from({ length: 24 }, (_, h) => ({
  hour: `${h}:00`,
  expected: Math.round(6 + 5 * Math.sin((h - 8) / 3)),
  actual: h < 12 ? Math.round(6 + 5 * Math.sin((h - 8) / 3)) : 0,
}));

export function VelocityChart({ data = placeholder }: { data?: typeof placeholder }) {
  return (
    <div className="h-72 rounded-xl border border-scout-border bg-scout-surface p-4">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E4E4E7" />
          <XAxis dataKey="hour" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="expected" stroke="#7C3AED" dot={false} />
          <Line type="monotone" dataKey="actual" stroke="#E11D48" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
