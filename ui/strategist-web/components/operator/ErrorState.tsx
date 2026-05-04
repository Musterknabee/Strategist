export function ErrorState({ title, message }: { title: string; message: string }) {
  return (
    <section className="panel panel-error">
      <h3>{title}</h3>
      <p>{message}</p>
    </section>
  );
}
