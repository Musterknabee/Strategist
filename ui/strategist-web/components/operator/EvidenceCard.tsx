import type { ReactNode } from "react";

export function EvidenceCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="panel evidence-card">
      <h2>{title}</h2>
      {children}
    </section>
  );
}
