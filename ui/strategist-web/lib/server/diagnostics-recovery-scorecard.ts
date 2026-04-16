import { buildFrontendDiagnosticsActionQueue } from "@/lib/server/diagnostics-action-queue";
import { buildFrontendDiagnosticsEscalationMatrix } from "@/lib/server/diagnostics-escalation-matrix";
import { buildFrontendDiagnosticsIncidentPlaybook } from "@/lib/server/diagnostics-incident-playbook";
import { readLatestFrontendDiagnosticsHistoryEntry } from "@/lib/server/diagnostics-history";

export type FrontendDiagnosticsRecoveryCheck = {
  id: string;
  title: string;
  status: "pass" | "watch" | "fail";
  detail: string;
  route: string;
  command?: string;
};

export type FrontendDiagnosticsRecoveryScorecard = {
  generatedAt: string;
  latest: Awaited<ReturnType<typeof readLatestFrontendDiagnosticsHistoryEntry>>;
  queue: Awaited<ReturnType<typeof buildFrontendDiagnosticsActionQueue>>;
  escalation: Awaited<ReturnType<typeof buildFrontendDiagnosticsEscalationMatrix>>;
  playbook: Awaited<ReturnType<typeof buildFrontendDiagnosticsIncidentPlaybook>>;
  readiness: {
    score: number;
    maxScore: number;
    label: "ready" | "stabilizing" | "blocked";
  };
  checks: FrontendDiagnosticsRecoveryCheck[];
  notes: string[];
  stabilizeAndValidate: string;
};

export async function buildFrontendDiagnosticsRecoveryScorecard(): Promise<FrontendDiagnosticsRecoveryScorecard> {
  const [latest, queue, escalation, playbook] = await Promise.all([
    readLatestFrontendDiagnosticsHistoryEntry(),
    buildFrontendDiagnosticsActionQueue(),
    buildFrontendDiagnosticsEscalationMatrix(),
    buildFrontendDiagnosticsIncidentPlaybook(),
  ]);

  const checks: FrontendDiagnosticsRecoveryCheck[] = [];

  checks.push(
    latest
      ? {
          id: "latest-snapshot",
          title: "Latest diagnostics snapshot exists",
          status: "pass",
          detail: `Latest run posture is ${latest.posture} in ${latest.mode} mode at ${latest.generatedAt}.`,
          route: "/settings/latest",
        }
      : {
          id: "latest-snapshot",
          title: "Latest diagnostics snapshot exists",
          status: "fail",
          detail: "No diagnostics snapshot exists yet. Bootstrap, run smoke checks, and export a first snapshot.",
          route: "/settings/latest",
          command: "npm run bootstrap:env && npm run doctor && npm run dev && npm run smoke && npm run export:diagnostics",
        }
  );

  if (latest?.posture === "ok") {
    checks.push({
      id: "latest-posture",
      title: "Latest posture is healthy",
      status: "pass",
      detail: "Latest diagnostics posture is ok, so recovery can proceed into full validation if other checks hold.",
      route: "/settings/compare",
    });
  } else if (latest) {
    checks.push({
      id: "latest-posture",
      title: "Latest posture is healthy",
      status: "watch",
      detail: `Latest posture is ${latest.posture}; use compare, recommendations, and the incident playbook before trusting the shell.`,
      route: "/settings/incident-playbook",
      command: "npm run doctor && npm run smoke && npm run export:diagnostics && npm run recommend:diagnostics",
    });
  }

  if (queue.summary.queued === 0) {
    checks.push({
      id: "queued-actions",
      title: "No queued diagnostics blockers remain",
      status: "pass",
      detail: "Action queue has no queued items blocking recovery posture.",
      route: "/settings/action-queue",
    });
  } else if (queue.summary.queued <= 2) {
    checks.push({
      id: "queued-actions",
      title: "Queued diagnostics blockers are limited",
      status: "watch",
      detail: `There are ${queue.summary.queued} queued diagnostics actions still pending.`,
      route: "/settings/action-queue",
      command: "npm run recommend:diagnostics && npm run summarize:diagnostics",
    });
  } else {
    checks.push({
      id: "queued-actions",
      title: "Queued diagnostics blockers are limited",
      status: "fail",
      detail: `There are ${queue.summary.queued} queued diagnostics actions pending, which is too high for confident recovery posture.`,
      route: "/settings/action-queue",
      command: "npm run recommend:diagnostics && npm run export:diagnostics && npm run summarize:diagnostics",
    });
  }

  if (["monitor", "stabilize"].includes(escalation.currentLevel)) {
    checks.push({
      id: "escalation-level",
      title: "Escalation level is recoverable",
      status: escalation.currentLevel === "monitor" ? "pass" : "watch",
      detail: `Current escalation level is ${escalation.currentLevel}.`,
      route: "/settings/escalation-matrix",
    });
  } else {
    checks.push({
      id: "escalation-level",
      title: "Escalation level is recoverable",
      status: "fail",
      detail: `Current escalation level is ${escalation.currentLevel}; use the incident playbook before treating the console as stabilized.`,
      route: "/settings/incident-playbook",
      command: "npm run doctor && npm run smoke && npm run export:diagnostics && npm run recommend:diagnostics",
    });
  }

  checks.push({
    id: "playbook-loop",
    title: "Recovery loop is ready to run",
    status: latest ? "pass" : "watch",
    detail: `Incident playbook exposes ${playbook.steps.length} ordered steps for the current recovery posture.`,
    route: "/settings/incident-playbook",
    command: playbook.steps.find((step) => step.command)?.command,
  });

  const maxScore = checks.length;
  const score = checks.reduce((acc, check) => acc + (check.status === "pass" ? 1 : check.status === "watch" ? 0.5 : 0), 0);
  const label = score >= maxScore - 0.5 ? "ready" : score >= maxScore / 2 ? "stabilizing" : "blocked";

  const notes = [
    label === "ready"
      ? "Recovery scorecard indicates the shell is ready to continue into fuller validation steps."
      : label === "stabilizing"
        ? "Recovery scorecard indicates partial stabilization; clear watch/fail checks before trusting the console fully."
        : "Recovery scorecard indicates the console is still blocked; use the incident playbook and escalation matrix before proceeding.",
    `Latest mode is ${latest?.mode ?? "unknown"}; keep backend-connected and mock-backed runs clearly separated when reviewing recovery posture.`,
    `Queued diagnostics actions: ${queue.summary.queued}, warning pressure: ${escalation.warningPressure}.`,
  ];

  return {
    generatedAt: new Date().toISOString(),
    latest,
    queue,
    escalation,
    playbook,
    readiness: { score, maxScore, label },
    checks,
    notes,
    stabilizeAndValidate: [
      "npm run doctor",
      "npm run smoke",
      "npm run export:diagnostics",
      "npm run summarize:diagnostics",
      "npm run recommend:diagnostics",
      "npm run check",
    ].join(" && "),
  };
}
