import type { ReactNode } from "react";

export function MetricCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
}) {
  return (
    <div className="metric-card">
      <span className="metric-card__label">{label}</span>
      <span className="metric-card__value">{value}</span>
      {hint && <span className="metric-card__hint muted">{hint}</span>}
    </div>
  );
}
