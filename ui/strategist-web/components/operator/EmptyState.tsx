export function EmptyState({ title, detail }: { title: string; detail?: string }) {
  return (
    <section className="panel empty-state">
      <h3>{title}</h3>
      {detail && <p className="muted">{detail}</p>}
    </section>
  );
}
