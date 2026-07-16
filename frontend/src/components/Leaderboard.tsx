/**
 * Ranks models by correctness for one experiment — the MODEL COMPARISON
 * view from the project brief. Rows use ModelChannelTag so a model's
 * color here matches its color in every other visualization.
 *
 * Belongs to: frontend/src/components/
 * Phase: 7 (Frontend)
 */
import type { ModelComparisonRow } from "../types";
import ModelChannelTag from "./ModelChannelTag";

function formatPercent(value: number | null): string {
  return value === null ? "—" : `${(value * 100).toFixed(0)}%`;
}

function formatSeconds(value: number | null): string {
  return value === null ? "—" : `${value.toFixed(3)}s`;
}

export default function Leaderboard({ rows }: { rows: ModelComparisonRow[] }) {
  if (rows.length === 0) {
    return (
      <div className="border border-line bg-paper rounded-lg p-6 text-center text-mist font-mono text-sm">
        No solutions yet — run generation to populate the leaderboard.
      </div>
    );
  }

  return (
    <table className="w-full border border-line bg-paper rounded-lg overflow-hidden text-sm">
      <thead>
        <tr className="border-b border-line text-left text-xs uppercase tracking-wide text-mist">
          <th className="px-4 py-3 font-sans font-medium">Model</th>
          <th className="px-4 py-3 font-sans font-medium">Correctness</th>
          <th className="px-4 py-3 font-sans font-medium">Avg. Runtime</th>
          <th className="px-4 py-3 font-sans font-medium">Complexity</th>
          <th className="px-4 py-3 font-sans font-medium">Solutions</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={row.model} className={i !== rows.length - 1 ? "border-b border-line" : ""}>
            <td className="px-4 py-3">
              <ModelChannelTag modelName={row.model} />
            </td>
            <td className="px-4 py-3 font-mono text-graphite">{formatPercent(row.correctness)}</td>
            <td className="px-4 py-3 font-mono text-graphite">{formatSeconds(row.avg_runtime_s)}</td>
            <td className="px-4 py-3 font-mono text-graphite">{row.complexity ?? "—"}</td>
            <td className="px-4 py-3 font-mono text-mist">{row.n_solutions}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
