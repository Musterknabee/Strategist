/** Show digest prefix only (never full secrets). */
export function DigestDisplay({ prefix, label }: { prefix: string | null | undefined; label?: string }) {
  if (!prefix) return <span className="muted">—</span>;
  return (
    <code className="digest-display" title={label}>
      {prefix}
    </code>
  );
}
