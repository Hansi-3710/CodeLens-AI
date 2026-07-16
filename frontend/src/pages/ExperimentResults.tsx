/**
 * The MODEL COMPARISON view for one experiment: leaderboard + a
 * correctness chart, plus a "Generate" action while the experiment is
 * still pending.
 *
 * Belongs to: frontend/src/pages/
 * Phase: 7 (Frontend)
 */
import { Link, useParams } from "react-router-dom";
import Chart from "../components/Chart";
import Leaderboard from "../components/Leaderboard";
import { useExperiment, useGenerate, useResults } from "../api/hooks";

export default function ExperimentResults() {
  const { id } = useParams<{ id: string }>();
  const { data: experiment } = useExperiment(id);
  const { data: results, isLoading } = useResults(id);
  const generate = useGenerate(id!);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-mono text-xl text-paper">{experiment?.name ?? "Experiment"}</h1>
          <p className="text-sm text-mist mt-1 font-mono">status: {experiment?.status}</p>
        </div>
        <div className="flex gap-2">
          {experiment?.status === "pending" && (
            <button
              onClick={() => generate.mutate()}
              disabled={generate.isPending}
              className="bg-signal text-white text-sm font-medium rounded px-4 py-2 disabled:opacity-50 hover:opacity-90 transition-opacity"
            >
              {generate.isPending ? "Generating…" : "Run generation"}
            </button>
          )}
          <Link
            to={`/experiments/${id}/compare`}
            className="border border-line text-graphite bg-paper text-sm font-medium rounded px-4 py-2 hover:border-signal transition-colors"
          >
            Compare code
          </Link>
          <Link
            to={`/experiments/${id}/visualize`}
            className="border border-line text-graphite bg-paper text-sm font-medium rounded px-4 py-2 hover:border-signal transition-colors"
          >
            Visualize
          </Link>
        </div>
      </div>

      {experiment?.status === "running" && (
        <p className="text-signal text-sm font-mono mb-4">Generating solutions across all selected models…</p>
      )}

      {isLoading && <p className="text-mist font-mono text-sm">Loading results…</p>}

      {results && (
        <div className="space-y-6">
          <Leaderboard rows={results.models} />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Chart rows={results.models} metric="correctness" label="Correctness" />
            <Chart rows={results.models} metric="avg_runtime_s" label="Average runtime (s)" />
          </div>
        </div>
      )}
    </div>
  );
}
