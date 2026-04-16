import { readLatestFrontendDiagnosticsHistoryEntry } from "@/lib/server/diagnostics-history";
import { buildFrontendDiagnosticsSummary } from "@/lib/server/diagnostics-summary";

export type FrontendDiagnosticsCompare = {
  generatedAt: string;
  latest: Awaited<ReturnType<typeof readLatestFrontendDiagnosticsHistoryEntry>>;
  summary: Awaited<ReturnType<typeof buildFrontendDiagnosticsSummary>>;
  postureAligned: boolean;
  modeAligned: boolean;
  warningPressure: "none" | "moderate" | "high";
  notes: string[];
};

export async function buildFrontendDiagnosticsCompare(): Promise<FrontendDiagnosticsCompare> {
  const [latest, summary] = await Promise.all([
    readLatestFrontendDiagnosticsHistoryEntry(),
    buildFrontendDiagnosticsSummary(),
  ]);

  const postureAligned = !latest || !summary.latestPosture || latest.posture === summary.latestPosture;
  const modeAligned = !latest || !summary.latestMode || latest.mode === summary.latestMode;
  const warningPressure =
    summary.warningRuns >= 5 ? "high" : summary.warningRuns >= 2 ? "moderate" : "none";

  const notes: string[] = [];
  if (!latest) {
    notes.push("No diagnostics history exists yet. Export a first diagnostics snapshot before comparing latest vs aggregate posture.");
  } else {
    notes.push(
      postureAligned
        ? "Latest posture matches the aggregate latest posture derived from history."
        : "Latest posture differs from the aggregate summary posture. Review the latest export and summary together."
    );
    notes.push(
      modeAligned
        ? "Latest mode matches the summary-mode view."
        : "Latest mode differs from the aggregate summary-mode view. Confirm whether your current run changed backend/mock posture."
    );
    if (warningPressure === "high") {
      notes.push("Warning pressure is high across recent runs. Consider pruning noise only after reviewing repeated warning patterns.");
    } else if (warningPressure === "moderate") {
      notes.push("Warnings are present across recent runs. Review summary/history before treating the latest snapshot as healthy.");
    } else {
      notes.push("Warning pressure is low across recent runs.");
    }
  }

  return {
    generatedAt: new Date().toISOString(),
    latest,
    summary,
    postureAligned,
    modeAligned,
    warningPressure,
    notes,
  };
}
