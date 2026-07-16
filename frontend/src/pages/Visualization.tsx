/**
 * The "how do models diverge" view: statistical summary cards, the
 * similarity heatmap, and the diversity map (2D UMAP scatter, colored by
 * cluster and shaped by model channel color).
 *
 * Belongs to: frontend/src/pages/
 * Phase: 7 (Frontend)
 */
import { useParams } from "react-router-dom";
import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from "recharts";
import MetricCard from "../components/MetricCard";
import SimilarityHeatmap from "../components/SimilarityHeatmap";
import { channelColorFor } from "../lib/channelColor";
import { useAnalytics, useClusters, useSimilarity } from "../api/hooks";

function fmt(value: number | null | undefined, digits = 2): string {
  return value === null || value === undefined ? "—" : value.toFixed(digits);
}

export default function Visualization() {
  const { id } = useParams<{ id: string }>();
  const { data: analytics } = useAnalytics(id);
  const { data: similarity } = useSimilarity(id);
  const { data: clusters } = useClusters(id);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-mono text-xl text-paper mb-1">Visualize</h1>
        <p className="text-sm text-mist">Where models agree, where they diverge, and why.</p>
      </div>

      {analytics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="Solutions" value={String(analytics.n_solutions)} />
          <MetricCard
            label="Avg. pass rate"
            value={analytics.pass_rate.mean !== null ? `${(analytics.pass_rate.mean * 100).toFixed(0)}%` : "—"}
            caption={
              analytics.pass_rate.n > 0
                ? `95% CI [${fmt((analytics.pass_rate.ci_95_low ?? 0) * 100, 0)}%, ${fmt((analytics.pass_rate.ci_95_high ?? 0) * 100, 0)}%]`
                : undefined
            }
          />
          <MetricCard
            label="Length vs. pass rate"
            value={fmt(analytics.correlations.code_length_vs_pass_rate.pearson_r)}
            caption="Pearson r"
          />
          <MetricCard
            label="Model fingerprint"
            value={
              analytics.model_fingerprint.sufficient_data
                ? `${((analytics.model_fingerprint.cv_accuracy ?? 0) * 100).toFixed(0)}%`
                : "n/a"
            }
            caption={
              analytics.model_fingerprint.sufficient_data
                ? `baseline ${((analytics.model_fingerprint.baseline_accuracy ?? 0) * 100).toFixed(0)}%`
                : "needs more solutions"
            }
          />
        </div>
      )}

      {similarity && <SimilarityHeatmap pairs={similarity.pairs} />}

      <div className="border border-line bg-paper rounded-lg p-4">
        <div className="text-xs uppercase tracking-wide text-mist font-sans mb-3">
          Diversity map (2D projection of solution embeddings)
        </div>
        {clusters?.points.length ? (
          <ResponsiveContainer width="100%" height={320}>
            <ScatterChart margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E4E1D8" />
              <XAxis type="number" dataKey="x" tick={{ fontFamily: "JetBrains Mono", fontSize: 11, fill: "#9AA0AC" }} />
              <YAxis type="number" dataKey="y" tick={{ fontFamily: "JetBrains Mono", fontSize: 11, fill: "#9AA0AC" }} />
              <ZAxis range={[80, 80]} />
              <Tooltip
                contentStyle={{ fontFamily: "JetBrains Mono", fontSize: 12, borderColor: "#E4E1D8" }}
                formatter={(_value, _name, item: any) => [item.payload.model, "model"]}
              />
              <Scatter
                data={clusters.points}
                fill="#4F7CFF"
                shape={(props: any) => (
                  <circle cx={props.cx} cy={props.cy} r={6} fill={channelColorFor(props.payload.model)} />
                )}
              />
            </ScatterChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-sm text-mist font-mono">
            {clusters?.note ?? "No embeddings available yet."}
          </p>
        )}
      </div>
    </div>
  );
}
