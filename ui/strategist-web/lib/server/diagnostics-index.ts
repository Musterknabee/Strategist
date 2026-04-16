import { getFrontendDiagnosticsManifest } from "@/lib/diagnostics";
import { buildFrontendDiagnosticsSummary } from "@/lib/server/diagnostics-summary";
import { readLatestFrontendDiagnosticsHistoryEntry } from "@/lib/server/diagnostics-history";

export type FrontendDiagnosticsIndex = {
  generatedAt: string;
  manifest: ReturnType<typeof getFrontendDiagnosticsManifest>;
  summary: Awaited<ReturnType<typeof buildFrontendDiagnosticsSummary>>;
  latest: Awaited<ReturnType<typeof readLatestFrontendDiagnosticsHistoryEntry>>;
  recommendedValidationSequence: string;
  notes: string[];
};

export async function buildFrontendDiagnosticsIndex(): Promise<FrontendDiagnosticsIndex> {
  const [summary, latest] = await Promise.all([
    buildFrontendDiagnosticsSummary(),
    readLatestFrontendDiagnosticsHistoryEntry(),
  ]);
  const manifest = getFrontendDiagnosticsManifest();

  return {
    generatedAt: new Date().toISOString(),
    manifest,
    summary,
    latest,
    recommendedValidationSequence: [
      'npm run bootstrap:env',
      'npm install',
      'npm run doctor',
      'npm run dev',
      'npm run smoke',
      'npm run check',
      'npm run build',
    ].join(' && '),
    notes: [
      'Use bootstrap plus doctor before the first local run so the shell starts from a known env posture.',
      'Use smoke once the dev server is running for a quick BFF sanity check before check/build.',
      'Use export/history/summary when you want a diagnostics trail instead of only the current runtime posture.',
    ],
  };
}
