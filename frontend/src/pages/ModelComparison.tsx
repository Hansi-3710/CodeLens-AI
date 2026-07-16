/**
 * Side-by-side code comparison: pick a problem, see every model's
 * solution to it at once — the direct answer to "how different are the
 * solutions models produce for the same task?"
 *
 * Belongs to: frontend/src/pages/
 * Phase: 7 (Frontend)
 */
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import CodeViewer from "../components/CodeViewer";
import { useSolutions } from "../api/hooks";

export default function ModelComparison() {
  const { id } = useParams<{ id: string }>();
  const { data: solutions, isLoading } = useSolutions(id);
  const [selectedPromptId, setSelectedPromptId] = useState<string | null>(null);

  const prompts = useMemo(() => {
    if (!solutions) return [];
    const seen = new Map<string, string>();
    solutions.forEach((s) => seen.set(s.prompt_id, s.problem_statement));
    return Array.from(seen.entries());
  }, [solutions]);

  const activePromptId = selectedPromptId ?? prompts[0]?.[0] ?? null;
  const visibleSolutions = solutions?.filter((s) => s.prompt_id === activePromptId) ?? [];

  return (
    <div>
      <h1 className="font-mono text-xl text-paper mb-6">Compare code</h1>

      {isLoading && <p className="text-mist font-mono text-sm">Loading…</p>}

      {prompts.length > 1 && (
        <div className="flex flex-wrap gap-2 mb-6">
          {prompts.map(([promptId, statement]) => (
            <button
              key={promptId}
              onClick={() => setSelectedPromptId(promptId)}
              className={`text-xs font-mono px-3 py-1.5 rounded border transition-colors max-w-xs truncate ${
                promptId === activePromptId
                  ? "bg-signal text-white border-signal"
                  : "border-line text-paper/70 hover:border-signal"
              }`}
              title={statement}
            >
              {statement}
            </button>
          ))}
        </div>
      )}

      {activePromptId && (
        <p className="text-sm text-mist mb-4 font-mono">
          {prompts.find(([pid]) => pid === activePromptId)?.[1]}
        </p>
      )}

      {visibleSolutions.length === 0 && !isLoading && (
        <p className="text-mist text-sm">No solutions yet — run generation from the experiment page first.</p>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {visibleSolutions.map((s) => (
          <CodeViewer key={s.id} modelName={s.model_name} code={s.code} />
        ))}
      </div>
    </div>
  );
}
