/**
 * Pairwise similarity heatmap — one row per model pair, colored by
 * similarity score. Axis labels use ModelChannelTag so a model's identity
 * carries over from the Leaderboard and Chart above it.
 *
 * Belongs to: frontend/src/components/
 * Phase: 7 (Frontend)
 */
import type { SimilarityPair } from "../types";
import ModelChannelTag from "./ModelChannelTag";

function cellShade(value: number): string {
  // Interpolates from near-white (dissimilar) to signal-blue (identical),
  // so higher similarity reads as visually "denser" without needing a legend.
  const alpha = Math.max(0.08, value);
  return `rgba(79, 124, 255, ${alpha})`;
}

export default function SimilarityHeatmap({ pairs }: { pairs: SimilarityPair[] }) {
  if (pairs.length === 0) {
    return (
      <div className="border border-line bg-paper rounded-lg p-6 text-center text-mist font-mono text-sm">
        No comparable solution pairs yet.
      </div>
    );
  }

  return (
    <div className="border border-line bg-paper rounded-lg p-4 overflow-x-auto">
      <div className="text-xs uppercase tracking-wide text-mist font-sans mb-3">
        Pairwise similarity (token / AST / embedding)
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-mist">
            <th className="px-3 py-2 font-sans font-medium">Pair</th>
            <th className="px-3 py-2 font-sans font-medium">Token</th>
            <th className="px-3 py-2 font-sans font-medium">AST</th>
            <th className="px-3 py-2 font-sans font-medium">Embedding</th>
          </tr>
        </thead>
        <tbody>
          {pairs.map((pair, i) => (
            <tr key={i} className="border-t border-line">
              <td className="px-3 py-2">
                <div className="flex items-center gap-2">
                  <ModelChannelTag modelName={pair.model_a} size="sm" />
                  <span className="text-mist">×</span>
                  <ModelChannelTag modelName={pair.model_b} size="sm" />
                </div>
              </td>
              {([pair.token_similarity, pair.ast_similarity, pair.embedding_similarity] as (number | null)[]).map(
                (value, j) => (
                  <td key={j} className="px-3 py-2">
                    {value === null ? (
                      <span className="text-mist font-mono text-xs">n/a</span>
                    ) : (
                      <div
                        className="font-mono text-xs text-graphite rounded px-2 py-1 inline-block min-w-[3.5rem] text-center"
                        style={{ backgroundColor: cellShade(value) }}
                      >
                        {(value * 100).toFixed(0)}%
                      </div>
                    )}
                  </td>
                )
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
