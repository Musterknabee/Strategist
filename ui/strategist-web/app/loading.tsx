import { ConsoleLoadingState } from "@/features/shared/components/console-state";

export default function GlobalLoading() {
  return (
    <div className="min-h-screen bg-zinc-950 p-8 text-zinc-100">
      <ConsoleLoadingState
        title="Loading Strategist"
        message="Hydrating shell providers, runtime posture, and projection-backed routes…"
      />
    </div>
  );
}
