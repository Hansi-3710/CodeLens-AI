/**
 * Monospace code display with a model-tagged header and lightweight
 * Python syntax highlighting (see lib/pythonHighlight.tsx — no heavy
 * highlighting library, to keep the bundle small).
 *
 * Belongs to: frontend/src/components/
 * Phase: 7 (Frontend); highlighting added in the post-audit hardening pass.
 */
import { highlightPython } from "../lib/pythonHighlight";
import ModelChannelTag from "./ModelChannelTag";

export default function CodeViewer({ modelName, code }: { modelName: string; code: string }) {
  return (
    <div className="border border-line bg-paper rounded-lg overflow-hidden">
      <div className="px-4 py-2 border-b border-line flex items-center justify-between bg-ink/[0.02]">
        <ModelChannelTag modelName={modelName} />
      </div>
      <pre className="p-4 text-sm font-mono text-graphite overflow-x-auto leading-relaxed">
        <code>{highlightPython(code)}</code>
      </pre>
    </div>
  );
}
