import { ConsoleLoadingState } from "@/features/shared/components/console-state";

export default function ConsoleRouteLoading() {
  return (
    <ConsoleLoadingState
      title="Loading console route"
      message="Hydrating the selected Strategist domain surface from projection-backed UI routes…"
    />
  );
}
