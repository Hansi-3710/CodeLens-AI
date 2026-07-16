/**
 * Bar chart comparing one metric across models, using each model's
 * channel color for its bar.
 *
 * Belongs to: frontend/src/components/
 * Phase: 7 (Frontend)
 */
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { channelColorFor } from "../lib/channelColor";
import type { ModelComparisonRow } from "../types";

export default function Chart({
  rows,
  metric,
  label,
}: {
  rows: ModelComparisonRow[];
  metric: "correctness" | "avg_runtime_s";
  label: string;
}) {
  const data = rows.map((r) => ({ model: r.model, value: r[metric] ?? 0 }));

  return (
    <div className="border border-line bg-paper rounded-lg p-4">
      <div className="text-xs uppercase tracking-wide text-mist font-sans mb-3">{label}</div>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E4E1D8" vertical={false} />
          <XAxis dataKey="model" tick={{ fontFamily: "JetBrains Mono", fontSize: 11, fill: "#9AA0AC" }} />
          <YAxis tick={{ fontFamily: "JetBrains Mono", fontSize: 11, fill: "#9AA0AC" }} />
          <Tooltip
            contentStyle={{ fontFamily: "JetBrains Mono", fontSize: 12, borderColor: "#E4E1D8" }}
            formatter={(value: number) => value.toFixed(3)}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((entry) => (
              <Cell key={entry.model} fill={channelColorFor(entry.model)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
