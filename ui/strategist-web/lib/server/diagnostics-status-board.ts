import { buildFrontendDiagnosticsCompare } from "@/lib/server/diagnostics-compare";
import { readLatestFrontendDiagnosticsHistoryEntry } from "@/lib/server/diagnostics-history";
import { buildFrontendDiagnosticsSummary } from "@/lib/server/diagnostics-summary";
import { buildFrontendDiagnosticsTrends } from "@/lib/server/diagnostics-trends";

export type FrontendDiagnosticsStatusBoard = {
  generatedAt: string;
  latest: Awaited<ReturnType<typeof readLatestFrontendDiagnosticsHistoryEntry>>;
  summary: Awaited<ReturnType<typeof buildFrontendDiagnosticsSummary>>;
  trends: Awaited<ReturnType<typeof buildFrontendDiagnosticsTrends>>;
  compare: Awaited<ReturnType<typeof buildFrontendDiagnosticsCompare>>;
  maintenanceLoop: string;
  statusNotes: string[];
};

export async function buildFrontendDiagnosticsStatusBoard(): Promise<FrontendDiagnosticsStatusBoard> {
  const [latest, summary, trends, compare] = await Promise.all([
    readLatestFrontendDiagnosticsHistoryEntry(),
    buildFrontendDiagnosticsSummary(),
    buildFrontendDiagnosticsTrends(),
    buildFrontendDiagnosticsCompare(),
  ]);

  const statusNotes: string[] = [];
  if (!latest) {
    statusNotes.push("No diagnostics export exists yet. Start with bootstrap, doctor, dev, smoke, then export a first diagnostics snapshot.");
  } else {
    statusNotes.push(`Latest run posture is ${latest.posture} in ${latest.mode} mode.`);
    statusNotes.push(
      compare.postureAligned
        ? "Latest posture aligns with the aggregate summary posture."
        : "Latest posture differs from the aggregate summary posture; review compare and history before treating this run as representative."
    );
    statusNotes.push(
      trends.trendPoints.length
        ? `Trend window covers ${trends.trendPoints.length} day buckets from ${trends.earliestDate} to ${trends.latestDate}.`
        : "Trend window is empty until diagnostics history exists."
    );
    if (summary.warningRuns > 0 || summary.attentionRuns > 0) {
      statusNotes.push(`Recent diagnostics trail includes ${summary.warningRuns} warning and ${summary.attentionRuns} attention runs.`);
    } else {
      statusNotes.push("Recent diagnostics trail shows no warning or attention runs.");
    }
  }

  return {
    generatedAt: new Date().toISOString(),
    latest,
    summary,
    trends,
    compare,
    maintenanceLoop: [
      'npm run doctor',
      'npm run dev',
      'npm run smoke',
      'npm run export:diagnostics',
      'npm run summarize:diagnostics',
      'npm run prune:diagnostics',
    ].join(' && '),
    statusNotes,
  };
}
