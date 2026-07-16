/**
 * Experiment creation form: name, one or more problem prompts, and which
 * registered models to compare — matches the project brief's input shape
 * (Problem / Language / Models).
 *
 * Belongs to: frontend/src/pages/
 * Phase: 7 (Frontend)
 */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCreateExperiment } from "../api/hooks";
import { useModels } from "../api/hooks";
import type { PromptInput } from "../types";

export default function CreateExperiment() {
  const { data: models } = useModels();
  const createExperiment = useCreateExperiment();
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [prompts, setPrompts] = useState<PromptInput[]>([{ problem_statement: "", language: "python" }]);
  const [selectedModels, setSelectedModels] = useState<string[]>([]);

  function updatePrompt(index: number, statement: string) {
    setPrompts((prev) => prev.map((p, i) => (i === index ? { ...p, problem_statement: statement } : p)));
  }

  function addPrompt() {
    setPrompts((prev) => [...prev, { problem_statement: "", language: "python" }]);
  }

  function toggleModel(name: string) {
    setSelectedModels((prev) => (prev.includes(name) ? prev.filter((m) => m !== name) : [...prev, name]));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const experiment = await createExperiment.mutateAsync({
      name,
      prompts: prompts.filter((p) => p.problem_statement.trim()),
      models: selectedModels,
    });
    navigate(`/experiments/${experiment.id}`);
  }

  const canSubmit = name.trim() && selectedModels.length > 0 && prompts.some((p) => p.problem_statement.trim());

  return (
    <div className="max-w-2xl">
      <h1 className="font-mono text-xl text-paper mb-6">New experiment</h1>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-paper border border-line rounded-lg p-6">
          <label className="block text-xs uppercase tracking-wide text-mist mb-1">Experiment name</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Shortest path comparison"
            className="w-full border border-line rounded px-3 py-2 text-sm font-mono focus:border-signal outline-none"
          />
        </div>

        <div className="bg-paper border border-line rounded-lg p-6">
          <label className="block text-xs uppercase tracking-wide text-mist mb-2">Problems</label>
          <div className="space-y-3">
            {prompts.map((p, i) => (
              <textarea
                key={i}
                value={p.problem_statement}
                onChange={(e) => updatePrompt(i, e.target.value)}
                placeholder="Implement a function that finds the shortest path between two nodes."
                rows={2}
                className="w-full border border-line rounded px-3 py-2 text-sm font-mono focus:border-signal outline-none resize-none"
              />
            ))}
          </div>
          <button
            type="button"
            onClick={addPrompt}
            className="text-xs font-mono text-signal mt-3 hover:underline"
          >
            + add another problem
          </button>
        </div>

        <div className="bg-paper border border-line rounded-lg p-6">
          <label className="block text-xs uppercase tracking-wide text-mist mb-2">Models to compare</label>
          <div className="flex flex-wrap gap-2">
            {models?.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => toggleModel(m.name)}
                className={`text-xs font-mono px-3 py-1.5 rounded border transition-colors ${
                  selectedModels.includes(m.name)
                    ? "bg-signal text-white border-signal"
                    : "border-line text-graphite hover:border-signal"
                }`}
              >
                {m.name}
              </button>
            ))}
            {models?.length === 0 && (
              <p className="text-sm text-mist">No models registered yet — register one via POST /models first.</p>
            )}
          </div>
        </div>

        <button
          type="submit"
          disabled={!canSubmit || createExperiment.isPending}
          className="bg-signal text-white text-sm font-medium rounded px-5 py-2.5 disabled:opacity-40 hover:opacity-90 transition-opacity"
        >
          {createExperiment.isPending ? "Creating…" : "Create experiment"}
        </button>
      </form>
    </div>
  );
}
