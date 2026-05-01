import { classifyOperationalStatus } from "@/lib/operator/payload-utils";

export function StatusBadge({ label, raw }: { label?: string; raw: string | null | undefined }) {
  const text = raw ?? "—";
  const tone = classifyOperationalStatus(text);
  return (
    <span className={`status-badge status-badge--${tone}`} title={label}>
      {text}
    </span>
  );
}
