import { buildFrontendDiagnosticsEscalationMatrix } from "@/lib/server/diagnostics-escalation-matrix";
import { buildFrontendDiagnosticsActionQueue } from "@/lib/server/diagnostics-action-queue";
import { buildFrontendDiagnosticsStatusBoard } from "@/lib/server/diagnostics-status-board";

export type DiagnosticsIncidentPlaybookStep = {
  id: string;
  title: string;
  description: string;
  route: string;
  command?: string;
};

export type FrontendDiagnosticsIncidentPlaybook = {
  generatedAt: string;
  currentLevel: string;
  latestPosture: string;
  latestMode: string;
  queuedCount: number;
  warningPressure: number;
  boardPosture: string;
  steps: DiagnosticsIncidentPlaybookStep[];
  notes: string[];
};

export async function buildFrontendDiagnosticsIncidentPlaybook(): Promise<FrontendDiagnosticsIncidentPlaybook> {
  const [matrix, queue, board] = await Promise.all([
    buildFrontendDiagnosticsEscalationMatrix(),
    buildFrontendDiagnosticsActionQueue(),
    buildFrontendDiagnosticsStatusBoard(),
  ]);

  const steps: DiagnosticsIncidentPlaybookStep[] = [
    {
      id: 'inspect-board',
      title: 'Inspect current board posture',
      description: 'Start from the status board to see current posture, mode, warning pressure, and maintenance notes.',
      route: '/settings/status-board',
    },
    {
      id: 'review-escalation',
      title: 'Review escalation matrix',
      description: 'Confirm whether the local frontend posture should remain monitor, stabilize, investigate, or reset.',
      route: '/settings/escalation-matrix',
    },
    {
      id: 'clear-action-queue',
      title: 'Work the diagnostics action queue',
      description: 'Execute or monitor the queued local actions before attempting a full validation pass.',
      route: '/settings/action-queue',
    },
    {
      id: 'stabilize-loop',
      title: 'Run the stabilize-and-validate loop',
      description: 'Use the recurring local loop when posture is recoverable without a full reset.',
      route: '/settings/runbook',
      command: 'npm run doctor && npm run smoke && npm run export:diagnostics && npm run summarize:diagnostics && npm run recommend:diagnostics && npm run check',
    },
    {
      id: 'reset-trail',
      title: 'Reset diagnostics artifacts when needed',
      description: 'Use a clean diagnostics trail only when escalation indicates reset posture or history is misleading.',
      route: '/settings/latest',
      command: 'npm run reset:diagnostics && npm run bootstrap:env && npm run doctor',
    },
  ];

  const notes = [
    `Current escalation level is ${matrix.currentLevel}; keep queued count (${queue.summary.queued}) and warning pressure (${matrix.warningPressure}) together when deciding the next move.`,
    `Status-board posture is ${board.latest?.posture ?? "unknown"} in ${board.latest?.mode ?? "unknown"} mode; prefer stabilize loops before reset unless escalation has already crossed into reset.`,
    'After each loop, export diagnostics again so the latest/history/summary pages reflect the new posture before deciding the next action.',
  ];

  return {
    generatedAt: new Date().toISOString(),
    currentLevel: matrix.currentLevel,
    latestPosture: matrix.latestPosture,
    latestMode: matrix.latestMode,
    queuedCount: queue.summary.queued,
    warningPressure: matrix.warningPressure,
    boardPosture: board.latest?.posture ?? "unknown",
    steps,
    notes,
  };
}
