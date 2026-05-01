export function Timestamp({ iso, label }: { iso: string | null | undefined; label?: string }) {
  if (!iso) return <span className="muted">—</span>;
  return (
    <time dateTime={iso} title={iso}>
      {label ? `${label}: ` : ""}
      {iso}
    </time>
  );
}
