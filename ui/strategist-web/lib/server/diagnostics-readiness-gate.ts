import { buildFrontendDiagnosticsRecoveryScorecard } from "@/lib/server/diagnostics-recovery-scorecard";
import { buildFrontendDiagnosticsStatusBoard } from "@/lib/server/diagnostics-status-board";
import { readLatestFrontendDiagnosticsHistoryEntry } from "@/lib/server/diagnostics-history";

export type FrontendDiagnosticsReadinessGate = {
  generatedAt: string;
  latest: Awaited<ReturnType<typeof readLatestFrontendDiagnosticsHistoryEntry>>;
  recovery: Awaited<ReturnType<typeof buildFrontendDiagnosticsRecoveryScorecard>>;
  statusBoard: Awaited<ReturnType<typeof buildFrontendDiagnosticsStatusBoard>>;
  decision: {
    level: "go" | "conditional" | "no-go";
    rationale: string;
  };
  blockers: Array<{
    id: string;
    title: string;
    detail: string;
    route: string;
    command?: string;
  }>;
  prerequisites: Array<{
    id: string;
    title: string;
    status: "met" | "watch" | "missing";
    detail: string;
    route: string;
  }>;
  proceedSequence: string;
  notes: string[];
};

export async function buildFrontendDiagnosticsReadinessGate(): Promise<FrontendDiagnosticsReadinessGate> {
  const [latest, recovery, statusBoard] = await Promise.all([
    readLatestFrontendDiagnosticsHistoryEntry(),
    buildFrontendDiagnosticsRecoveryScorecard(),
    buildFrontendDiagnosticsStatusBoard(),
  ]);

  const prerequisites = recovery.checks.map((check) => ({
    id: check.id,
    title: check.title,
    status: check.status === "pass" ? "met" as const : check.status === "watch" ? "watch" as const : "missing" as const,
    detail: check.detail,
    route: check.route,
  }));

  const blockers = recovery.checks
    .filter((check) => check.status !== "pass")
    .map((check) => ({
      id: check.id,
      title: check.title,
      detail: check.detail,
      route: check.route,
      command: check.command,
    }));

  let level: FrontendDiagnosticsReadinessGate["decision"]["level"] = "conditional";
  let rationale = "Recovery posture is partially stabilized; clear watch items before trusting a full validation pass.";

  if (recovery.readiness.label === "ready" && statusBoard.summary.latestPosture === "ok") {
    level = "go";
    rationale = "Latest posture is healthy and the recovery scorecard indicates the shell is ready for a fuller validation pass.";
  } else if (recovery.readiness.label === "blocked" || statusBoard.compare.warningPressure === "high") {
    level = "no-go";
    rationale = "Diagnostics posture is still blocked or warning pressure remains too high for a safe validation/build pass.";
  }

  const notes = [
    `Latest diagnostics posture: ${latest?.posture ?? "unknown"}; mode: ${latest?.mode ?? "unknown"}.`,
    `Recovery label is ${recovery.readiness.label} with score ${recovery.readiness.score}/${recovery.readiness.maxScore}.`,
    `Status board latest posture is ${statusBoard.summary.latestPosture ?? "unknown"} with warning pressure ${statusBoard.compare.warningPressure}.`,
    level === "go"
      ? "Proceed into check/build, but still preserve the latest snapshot and compare it against summary history afterward."
      : level === "conditional"
        ? "Treat this as a controlled conditional go: run doctor/smoke/export first, then reassess blockers before build."
        : "Do not proceed directly to build; use the action queue, incident playbook, and recovery scorecard to clear blockers first.",
  ];

  return {
    generatedAt: new Date().toISOString(),
    latest,
    recovery,
    statusBoard,
    decision: { level, rationale },
    blockers,
    prerequisites,
    proceedSequence: [
      "npm run doctor",
      "npm run smoke",
      "npm run export:diagnostics",
      level === "go" ? "npm run check" : "npm run recommend:diagnostics",
      level === "go" ? "npm run build" : "npm run summarize:diagnostics",
    ].join(" && "),
    notes,
  };
}
