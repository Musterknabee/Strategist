import { buildFrontendDiagnosticsReadinessGate } from "@/lib/server/diagnostics-readiness-gate";
import { buildFrontendDiagnosticsDecisionLog } from "@/lib/server/diagnostics-decision-log";
import { buildFrontendDiagnosticsHandoffPacket } from "@/lib/server/diagnostics-handoff-packet";
import { buildFrontendDiagnosticsSummary } from "@/lib/server/diagnostics-summary";
import { readLatestFrontendDiagnosticsHistoryEntry } from "@/lib/server/diagnostics-history";

export type FrontendDiagnosticsCheckpointEntry = {
  id: string;
  label: string;
  status: "ready" | "watch" | "blocked";
  detail: string;
  supportingRoute: string;
  command?: string;
};

export type FrontendDiagnosticsCheckpointRegister = {
  generatedAt: string;
  latest: Awaited<ReturnType<typeof readLatestFrontendDiagnosticsHistoryEntry>>;
  summary: Awaited<ReturnType<typeof buildFrontendDiagnosticsSummary>>;
  readiness: Awaited<ReturnType<typeof buildFrontendDiagnosticsReadinessGate>>;
  decisionLog: Awaited<ReturnType<typeof buildFrontendDiagnosticsDecisionLog>>;
  handoff: Awaited<ReturnType<typeof buildFrontendDiagnosticsHandoffPacket>>;
  checkpoints: FrontendDiagnosticsCheckpointEntry[];
  checkpointBeforeProceedSequence: string;
  notes: string[];
};

export async function buildFrontendDiagnosticsCheckpointRegister(): Promise<FrontendDiagnosticsCheckpointRegister> {
  const [latest, summary, readiness, decisionLog, handoff] = await Promise.all([
    readLatestFrontendDiagnosticsHistoryEntry(),
    buildFrontendDiagnosticsSummary(),
    buildFrontendDiagnosticsReadinessGate(),
    buildFrontendDiagnosticsDecisionLog(),
    buildFrontendDiagnosticsHandoffPacket(),
  ]);

  const checkpoints: FrontendDiagnosticsCheckpointEntry[] = [
    {
      id: 'latest-posture',
      label: 'Latest diagnostics posture',
      status: latest?.posture === 'ok' ? 'ready' : latest?.posture === 'warning' ? 'watch' : 'blocked',
      detail: `Latest posture is ${latest?.posture ?? 'unknown'} in ${latest?.mode ?? 'unknown'} mode.`,
      supportingRoute: '/settings/latest',
    },
    {
      id: 'readiness-gate',
      label: 'Readiness gate',
      status: readiness.decision.level === 'go' ? 'ready' : readiness.decision.level === 'conditional' ? 'watch' : 'blocked',
      detail: readiness.decision.rationale,
      supportingRoute: '/settings/readiness-gate',
      command: readiness.proceedSequence,
    },
    {
      id: 'decision-log',
      label: 'Decision log pressure',
      status: decisionLog.summary.holdEntries > 0 ? 'blocked' : decisionLog.summary.stabilizeEntries > 0 ? 'watch' : 'ready',
      detail: `Proceed=${decisionLog.summary.proceedEntries}, Hold=${decisionLog.summary.holdEntries}, Stabilize=${decisionLog.summary.stabilizeEntries}.`,
      supportingRoute: '/settings/decision-log',
      command: decisionLog.proceedOrHoldSequence,
    },
    {
      id: 'handoff-packet',
      label: 'Handoff packet posture',
      status: handoff.handoffLabel === 'proceed' ? 'ready' : handoff.handoffLabel === 'stabilize' ? 'watch' : 'blocked',
      detail: `Current handoff label is ${handoff.handoffLabel}.`,
      supportingRoute: '/settings/handoff-packet',
      command: handoff.proceedOrHoldSequence,
    },
    {
      id: 'history-pressure',
      label: 'History pressure',
      status: summary.warningRuns > 0 || summary.attentionRuns > 0 ? 'watch' : 'ready',
      detail: `History contains ${summary.warningRuns} warning runs and ${summary.attentionRuns} attention runs.`,
      supportingRoute: '/settings/summary',
    },
  ];

  const notes = [
    'Use this register as the final checkpoint list before trusting a proceed recommendation.',
    checkpoints.some((item) => item.status === 'blocked')
      ? 'At least one checkpoint is blocked; hold or stabilize before proceeding.'
      : checkpoints.some((item) => item.status === 'watch')
        ? 'Some checkpoints are in watch posture; continue with caution and preserve a handoff packet.'
        : 'All checkpoints are currently ready; you can proceed with the validation sequence if desired.',
    `Latest history summary posture is ${summary.latestPosture ?? 'unknown'}.`,
  ];

  return {
    generatedAt: new Date().toISOString(),
    latest,
    summary,
    readiness,
    decisionLog,
    handoff,
    checkpoints,
    checkpointBeforeProceedSequence: [
      'npm run recommend:diagnostics',
      'npm run export:diagnostics',
      'npm run summarize:diagnostics',
      'npm run check',
      'npm run build',
    ].join(' && '),
    notes,
  };
}
