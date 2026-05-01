export function WarningList({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <section className="panel panel-warn">
      <h3>{title}</h3>
      <ul className="compact-list">
        {items.map((w) => (
          <li key={w}>{w}</li>
        ))}
      </ul>
    </section>
  );
}
