import { readFrontendDiagnosticsHistory, type FrontendDiagnosticsHistoryEntry } from "@/lib/server/diagnostics-history";

export type FrontendDiagnosticsTrendPoint = {
  date: string;
  totalRuns: number;
  backendConnectedRuns: number;
  mockBackedRuns: number;
  warningRuns: number;
  attentionRuns: number;
  okRuns: number;
};

export type FrontendDiagnosticsTrends = {
  generatedAt: string;
  windowSize: number;
  totalEntries: number;
  latestDate: string | null;
  earliestDate: string | null;
  trendPoints: FrontendDiagnosticsTrendPoint[];
  notes: string[];
};

function toDateBucket(value: string): string { return value.slice(0, 10); }
function sortAsc(a: string, b: string): number { return a < b ? -1 : a > b ? 1 : 0; }

function buildTrendPoint(date: string, entries: FrontendDiagnosticsHistoryEntry[]): FrontendDiagnosticsTrendPoint {
  return {
    date,
    totalRuns: entries.length,
    backendConnectedRuns: entries.filter((entry) => entry.mode === "backend-connected").length,
    mockBackedRuns: entries.filter((entry) => entry.mode === "mock-backed").length,
    warningRuns: entries.filter((entry) => entry.posture === "warning").length,
    attentionRuns: entries.filter((entry) => entry.posture === "attention").length,
    okRuns: entries.filter((entry) => entry.posture === "ok").length,
  };
}

export async function buildFrontendDiagnosticsTrends(windowSize = 30): Promise<FrontendDiagnosticsTrends> {
  const history = await readFrontendDiagnosticsHistory({ limit: 500 });
  const byDate = new Map<string, FrontendDiagnosticsHistoryEntry[]>();
  for (const entry of history) {
    const date = toDateBucket(entry.generatedAt);
    const bucket = byDate.get(date) ?? [];
    bucket.push(entry);
    byDate.set(date, bucket);
  }
  const trendPoints = Array.from(byDate.entries())
    .sort(([left], [right]) => sortAsc(left, right))
    .slice(-windowSize)
    .map(([date, entries]) => buildTrendPoint(date, entries));
  const latestDate = trendPoints.length ? trendPoints[trendPoints.length - 1]?.date ?? null : null;
  const earliestDate = trendPoints.length ? trendPoints[0]?.date ?? null : null;

  const notes: string[] = [];
  if (!trendPoints.length) {
    notes.push("No diagnostics history exists yet. Export at least one diagnostics snapshot before using trends.");
  } else {
    const warningDays = trendPoints.filter((point) => point.warningRuns > 0 || point.attentionRuns > 0).length;
    const backendDays = trendPoints.filter((point) => point.backendConnectedRuns > 0).length;
    notes.push(`Trend window covers ${trendPoints.length} day buckets from ${earliestDate} to ${latestDate}.`);
    notes.push(`Backend-connected runs appeared on ${backendDays} of ${trendPoints.length} tracked day buckets.`);
    notes.push(
      warningDays > 0
        ? `Warning or attention posture appeared on ${warningDays} day buckets. Compare with /settings/summary when deciding whether issues are isolated or repeated.`
        : "No warning or attention posture appears in the current trend window."
    );
  }

  return { generatedAt: new Date().toISOString(), windowSize, totalEntries: history.length, latestDate, earliestDate, trendPoints, notes };
}
