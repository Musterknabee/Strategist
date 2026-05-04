"use client";

/** Read-only JSON preview for operator diagnostics (no secrets redaction here — rely on backend read-plane). */
export function JsonPanel({
  title,
  data,
  schemaHint,
}: {
  title: string;
  data: unknown;
  schemaHint?: string;
}) {
  return (
    <section className="panel">
      <h2>{title}</h2>
      {schemaHint && <p className="muted">{schemaHint}</p>}
      <pre className="json-preview">{JSON.stringify(data, null, 2)}</pre>
    </section>
  );
}
