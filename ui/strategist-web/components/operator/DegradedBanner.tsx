export function DegradedBanner({ message }: { message: string }) {
  return (
    <section className="panel panel-warn degraded-banner" role="status">
      <strong>Degraded</strong>
      <p>{message}</p>
    </section>
  );
}
