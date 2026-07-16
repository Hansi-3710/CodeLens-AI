/**
 * Compact stat card — a label, a big monospace number, and an optional
 * sub-caption (e.g. a confidence interval).
 *
 * Belongs to: frontend/src/components/
 * Phase: 7 (Frontend)
 */
export default function MetricCard({
  label,
  value,
  caption,
}: {
  label: string;
  value: string;
  caption?: string;
}) {
  return (
    <div className="border border-line bg-paper rounded-lg px-5 py-4">
      <div className="text-xs uppercase tracking-wide text-mist font-sans">{label}</div>
      <div className="text-2xl font-mono font-semibold text-graphite mt-1">{value}</div>
      {caption && <div className="text-xs text-mist font-mono mt-1">{caption}</div>}
    </div>
  );
}
