import { buildFrontendDiagnosticsReadinessGate } from "@/lib/server/diagnostics-readiness-gate";
import { buildFrontendDiagnosticsRecoveryScorecard } from "@/lib/server/diagnostics-recovery-scorecard";
import { buildFrontendDiagnosticsActionQueue } from "@/lib/server/diagnostics-action-queue";

export type FrontendDiagnosticsDecisionLogEntry = {
  id: string;
  timestamp: string;
  decisionType: "proceed" | "conditional" | "hold" | "stabilize";
  title: string;
  rationale: string;
  sourceRoute: string;
  supportingRoute?: string;
  command?: string;
};

export type FrontendDiagnosticsDecisionLog = {
  generatedAt: string;
  latestPosture: string;
  recoveryLabel: string;
  readinessLevel: "go" | "conditional" | "no-go";
  queuedActionCount: number;
  summary: {
    totalEntries: number;
    proceedEntries: number;
    conditionalEntries: number;
    holdEntries: number;
    stabilizeEntries: number;
  };
  entries: FrontendDiagnosticsDecisionLogEntry[];
  notes: string[];
  proceedOrHoldSequence: string;
};

export async function buildFrontendDiagnosticsDecisionLog(): Promise<FrontendDiagnosticsDecisionLog> {
  const [readiness, recovery, actionQueue] = await Promise.all([
    buildFrontendDiagnosticsReadinessGate(),
    buildFrontendDiagnosticsRecoveryScorecard(),
    buildFrontendDiagnosticsActionQueue(),
  ]);

  const now = new Date().toISOString();
  const entries: FrontendDiagnosticsDecisionLogEntry[] = [];

  entries.push({
    id: 'readiness-gate',
    timestamp: now,
    decisionType: readiness.decision.level === 'go' ? 'proceed' : readiness.decision.level === 'conditional' ? 'conditional' : 'hold',
    title: `Readiness gate: ${readiness.decision.level}`,
    rationale: readiness.decision.rationale,
    sourceRoute: '/settings/readiness-gate',
    supportingRoute: '/settings/recovery-scorecard',
    command: readiness.proceedSequence,
  });

  entries.push({
    id: 'recovery-scorecard',
    timestamp: now,
    decisionType: recovery.readiness.label === 'ready' ? 'proceed' : recovery.readiness.label === 'stabilizing' ? 'stabilize' : 'hold',
    title: `Recovery scorecard: ${recovery.readiness.label}`,
    rationale: recovery.notes[0] ?? 'Recovery posture evaluated from diagnostics recovery checks.',
    sourceRoute: '/settings/recovery-scorecard',
    supportingRoute: '/settings/incident-playbook',
    command: recovery.stabilizeAndValidate,
  });

  if (actionQueue.summary.queued > 0) {
    entries.push({
      id: 'action-queue',
      timestamp: now,
      decisionType: 'stabilize',
      title: `Action queue: ${actionQueue.summary.queued} queued actions`,
      rationale: 'Queued diagnostics actions still require operator attention before trusting a fuller validation/build pass.',
      sourceRoute: '/settings/action-queue',
      supportingRoute: '/settings/recommendations',
      command: 'npm run recommend:diagnostics && npm run summarize:diagnostics',
    });
  }

  if (readiness.blockers.length) {
    entries.push({
      id: 'blockers',
      timestamp: now,
      decisionType: 'hold',
      title: `Readiness blockers: ${readiness.blockers.length}`,
      rationale: 'One or more blockers remain unresolved; inspect the readiness gate and linked supporting routes before proceeding.',
      sourceRoute: '/settings/readiness-gate',
      supportingRoute: readiness.blockers[0]?.route,
      command: readiness.blockers[0]?.command,
    });
  }

  const summary = {
    totalEntries: entries.length,
    proceedEntries: entries.filter((entry) => entry.decisionType === 'proceed').length,
    conditionalEntries: entries.filter((entry) => entry.decisionType === 'conditional').length,
    holdEntries: entries.filter((entry) => entry.decisionType === 'hold').length,
    stabilizeEntries: entries.filter((entry) => entry.decisionType === 'stabilize').length,
  };


  const notes = [
    `Latest diagnostics posture is ${readiness.latest?.posture ?? 'unknown'} and readiness decision is ${readiness.decision.level}.`,
    `Recovery label is ${recovery.readiness.label} with ${actionQueue.summary.queued} queued actions still tracked in the diagnostics action queue.`,
    readiness.decision.level === 'go'
      ? 'Proceed decisions should still preserve diagnostics exports/history so the latest successful posture remains reviewable.'
      : 'Hold/conditional decisions should be treated as audit checkpoints; review the linked routes before trusting the shell for a fuller validation/build pass.',
  ];

  return {
    generatedAt: now,
    latestPosture: readiness.latest?.posture ?? 'unknown',
    recoveryLabel: recovery.readiness.label,
    readinessLevel: readiness.decision.level,
    queuedActionCount: actionQueue.summary.queued,
    summary,
    entries,
    notes,
    proceedOrHoldSequence:
      readiness.decision.level === 'go'
        ? readiness.proceedSequence
        : 'npm run recommend:diagnostics && npm run summarize:diagnostics && npm run export:diagnostics && npm run doctor',
  };
}
