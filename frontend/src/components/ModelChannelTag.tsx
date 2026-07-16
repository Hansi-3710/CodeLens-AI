/**
 * The platform's signature element: a colored "channel" bar + monospace
 * model name, used identically in the Leaderboard, SimilarityHeatmap, and
 * diversity map — so a model's visual identity carries across every
 * different view without the reader re-learning a legend each time.
 *
 * Belongs to: frontend/src/components/
 * Phase: 7 (Frontend)
 */
import { channelColorFor } from "../lib/channelColor";

export default function ModelChannelTag({ modelName, size = "md" }: { modelName: string; size?: "sm" | "md" }) {
  const color = channelColorFor(modelName);
  const textSize = size === "sm" ? "text-xs" : "text-sm";
  return (
    <span className="inline-flex items-center gap-2">
      <span className="inline-block w-1 h-4 rounded-sm" style={{ backgroundColor: color }} aria-hidden="true" />
      <span className={`font-mono ${textSize} text-graphite`}>{modelName}</span>
    </span>
  );
}
