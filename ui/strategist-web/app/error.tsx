"use client";

import { useEffect } from "react";

import { ConsoleErrorState } from "@/features/shared/components/console-state";

export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error("Strategist global UI error", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-zinc-950 p-8 text-zinc-100">
      <ConsoleErrorState
        title="Strategist shell error"
        message="A client-side route or shell boundary failed. Use the reset action below, then re-open the affected governed surface."
      />
      <div className="mt-4">
        <button
          type="button"
          onClick={reset}
          className="rounded-xl border border-zinc-700 px-4 py-2 text-sm text-zinc-200 hover:bg-zinc-900"
        >
          Reset shell boundary
        </button>
      </div>
    </div>
  );
}
