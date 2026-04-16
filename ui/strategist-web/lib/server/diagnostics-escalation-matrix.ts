import { buildFrontendDiagnosticsActionQueue } from "@/lib/server/diagnostics-action-queue";
import { buildFrontendDiagnosticsCompare } from "@/lib/server/diagnostics-compare";
import { buildFrontendDiagnosticsSummary } from "@/lib/server/diagnostics-summary";
import { readLatestFrontendDiagnosticsHistoryEntry } from "@/lib/server/diagnostics-history";

export type FrontendDiagnosticsEscalationLevel = "monitor" | "stabilize" | "investigate" | "reset";

export type FrontendDiagnosticsEscalationRule = {
  level: FrontendDiagnosticsEscalationLevel;
  title: string;
  trigger: string;
  rationale: string;
  recommendedRoute: string;
  recommendedCommand?: string;
};

export type FrontendDiagnosticsEscalationMatrix = {
  generatedAt: string;
  currentLevel: FrontendDiagnosticsEscalationLevel;
  latestPosture: string;
  latestMode: string;
  queuedCount: number;
  warningPressure: number;
  postureAligned: boolean;
  rules: FrontendDiagnosticsEscalationRule[];
  notes: string[];
};

function deriveCurrentLevel(input: {
  latestPosture: string;
  queuedCount: number;
  warningPressure: number;
  postureAligned: boolean;
}): FrontendDiagnosticsEscalationLevel {
  if (input.latestPosture === "attention" || input.queuedCount >= 3) return "reset";
  if (input.latestPosture === "warning" || !input.postureAligned) return "investigate";
  if (input.warningPressure > 0 || input.queuedCount > 0) return "stabilize";
  return "monitor";
}

export async function buildFrontendDiagnosticsEscalationMatrix(): Promise<FrontendDiagnosticsEscalationMatrix> {
  const [latest, summary, compare, actionQueue] = await Promise.all([
    readLatestFrontendDiagnosticsHistoryEntry(),
    buildFrontendDiagnosticsSummary(),
    buildFrontendDiagnosticsCompare(),
    buildFrontendDiagnosticsActionQueue(),
  ]);

  const latestPosture = latest?.posture ?? "none";
  const latestMode = latest?.mode ?? "unknown";
  const queuedCount = actionQueue.summary.queued;
  const warningPressure = summary.warningRuns + summary.attentionRuns;
  const postureAligned = compare.postureAligned;
  const currentLevel = deriveCurrentLevel({ latestPosture, queuedCount, warningPressure, postureAligned });

  const rules: FrontendDiagnosticsEscalationRule[] = [
    {
      level: "monitor",
      title: "Monitor posture",
      trigger: "Latest posture is ok and queue pressure is low.",
      rationale: "Keep the diagnostics trail healthy with smoke, summary, and trends review instead of disruptive resets.",
      recommendedRoute: "/settings/status-board",
      recommendedCommand: "npm run smoke && npm run summarize:diagnostics",
    },
    {
      level: "stabilize",
      title: "Stabilize posture",
      trigger: "Warnings exist or queued actions remain, but the shell is still broadly usable.",
      rationale: "Prefer focused maintenance and export/summarize loops before escalating into reset posture.",
      recommendedRoute: "/settings/action-queue",
      recommendedCommand: "npm run doctor && npm run smoke && npm run export:diagnostics && npm run summarize:diagnostics",
    },
    {
      level: "investigate",
      title: "Investigate drift",
      trigger: "Latest posture is warning or aggregate/compare alignment has drifted.",
      rationale: "Compare the latest run against the history trail and inspect the highest-priority recommendations before trusting the shell.",
      recommendedRoute: "/settings/compare",
      recommendedCommand: "npm run recommend:diagnostics && npm run export:diagnostics && npm run summarize:diagnostics",
    },
    {
      level: "reset",
      title: "Reset diagnostics trail",
      trigger: "Latest posture is attention or queue pressure is materially elevated.",
      rationale: "Clear the current diagnostics trail, restart from a clean env posture, and rebuild trust with doctor, smoke, and fresh exports.",
      recommendedRoute: "/settings/latest",
      recommendedCommand: "npm run reset:diagnostics && npm run doctor && npm run smoke && npm run export:diagnostics",
    },
  ];

  const notes = [
    `Current escalation level is ${currentLevel}.`,
    queuedCount
      ? `There are ${queuedCount} queued diagnostics actions contributing to the current escalation posture.`
      : "There are no queued diagnostics actions contributing to the current escalation posture.",
    postureAligned
      ? "Latest posture aligns with the aggregate summary posture."
      : "Latest posture diverges from the aggregate summary posture; compare and history review should precede trust decisions.",
    warningPressure
      ? `Diagnostics history currently contains ${warningPressure} warning/attention runs.`
      : "Diagnostics history currently contains no warning or attention runs.",
  ];

  return {
    generatedAt: new Date().toISOString(),
    currentLevel,
    latestPosture,
    latestMode,
    queuedCount,
    warningPressure,
    postureAligned,
    rules,
    notes,
  };
}
