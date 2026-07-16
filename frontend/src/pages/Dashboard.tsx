/**
 * Lists the researcher's experiments and links to creating a new one.
 *
 * Belongs to: frontend/src/pages/
 * Phase: 7 (Frontend)
 */
import { Link } from "react-router-dom";
import { useExperiments } from "../api/hooks";

const STATUS_STYLES: Record<string, string> = {
  pending: "text-mist",
  running: "text-signal",
  completed: "text-channel-3",
  failed: "text-channel-1",
};

export default function Dashboard() {
  const { data: experiments, isLoading, error } = useExperiments();

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-mono text-xl text-paper">Experiments</h1>
          <p className="text-sm text-mist mt-1">
            How different are the solutions modern LLMs produce for the same problem?
          </p>
        </div>
        <Link
          to="/experiments/new"
          className="bg-signal text-white text-sm font-medium rounded px-4 py-2 hover:opacity-90 transition-opacity"
        >
          New experiment
        </Link>
      </div>

      {isLoading && <p className="text-mist font-mono text-sm">Loading…</p>}
      {error && <p className="text-channel-1 font-mono text-sm">Couldn't load experiments.</p>}

      {experiments && experiments.length === 0 && (
        <div className="border border-dashed border-white/20 rounded-lg p-12 text-center">
          <p className="text-mist text-sm">No experiments yet. Create one to compare how models solve a problem.</p>
        </div>
      )}

      <div className="grid gap-3">
        {experiments?.map((exp) => (
          <Link
            key={exp.id}
            to={`/experiments/${exp.id}`}
            className="bg-paper border border-line rounded-lg px-5 py-4 flex items-center justify-between hover:border-signal transition-colors"
          >
            <div>
              <div className="font-mono text-sm text-graphite">{exp.name}</div>
              <div className="text-xs text-mist mt-0.5">{new Date(exp.created_at).toLocaleString()}</div>
            </div>
            <span className={`text-xs font-mono uppercase ${STATUS_STYLES[exp.status] ?? "text-mist"}`}>
              {exp.status}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
