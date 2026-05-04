"use client";

import { useState } from "react";

export function JsonDetails({ summary, data }: { summary: string; data: unknown }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="json-details-wrap">
      <button type="button" className="linkish json-details-toggle" onClick={() => setOpen(!open)} aria-expanded={open}>
        {open ? "▼" : "▶"} {summary}
      </button>
      {open && <pre className="json-preview">{JSON.stringify(data, null, 2)}</pre>}
    </div>
  );
}
