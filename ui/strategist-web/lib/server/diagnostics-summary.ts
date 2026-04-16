import { readFrontendDiagnosticsHistory, type FrontendDiagnosticsHistoryEntry } from "@/lib/server/diagnostics-history";

export type FrontendDiagnosticsSummary = {
  generatedAt: string;
  totalRuns: number;
  backendConnectedRuns: number;
  mockBackedRuns: number;
  warningRuns: number;
  attentionRuns: number;
  okRuns: number;
  latestExportId: string | null;
  latestGeneratedAt: string | null;
  latestPosture: string | null;
  latestMode: FrontendDiagnosticsHistoryEntry["mode"] | null;
  postureBreakdown: Array<{ posture: string; count: number }>;
};

export async function buildFrontendDiagnosticsSummary(limit = 200): Promise<FrontendDiagnosticsSummary> {
  const history = await readFrontendDiagnosticsHistory({ limit });
  const latest = history[0] ?? null;

  const postureCounts = new Map<string, number>();
  for (const entry of history) {
    postureCounts.set(entry.posture, (postureCounts.get(entry.posture) ?? 0) + 1);
  }

  return {
    generatedAt: new Date().toISOString(),
    totalRuns: history.length,
    backendConnectedRuns: history.filter((entry) => entry.mode === "backend-connected").length,
    mockBackedRuns: history.filter((entry) => entry.mode === "mock-backed").length,
    warningRuns: history.filter((entry) => entry.posture === "warning").length,
    attentionRuns: history.filter((entry) => entry.posture === "attention").length,
    okRuns: history.filter((entry) => entry.posture === "ok").length,
    latestExportId: latest?.exportId ?? null,
    latestGeneratedAt: latest?.generatedAt ?? null,
    latestPosture: latest?.posture ?? null,
    latestMode: latest?.mode ?? null,
    postureBreakdown: Array.from(postureCounts.entries())
      .map(([posture, count]) => ({ posture, count }))
      .sort((a, b) => (a.count < b.count ? 1 : -1)),
  };
}
