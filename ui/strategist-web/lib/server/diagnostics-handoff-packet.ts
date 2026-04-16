import { buildFrontendDiagnosticsReadinessGate } from "@/lib/server/diagnostics-readiness-gate";
import { buildFrontendDiagnosticsDecisionLog } from "@/lib/server/diagnostics-decision-log";
import { buildFrontendDiagnosticsSummary } from "@/lib/server/diagnostics-summary";
import { buildFrontendDiagnosticsCompare } from "@/lib/server/diagnostics-compare";
import { readLatestFrontendDiagnosticsHistoryEntry } from "@/lib/server/diagnostics-history";

export type FrontendDiagnosticsHandoffPacket = {
  generatedAt: string;
  packetId: string;
  latest: Awaited<ReturnType<typeof readLatestFrontendDiagnosticsHistoryEntry>>;
  summary: Awaited<ReturnType<typeof buildFrontendDiagnosticsSummary>>;
  compare: Awaited<ReturnType<typeof buildFrontendDiagnosticsCompare>>;
  readiness: Awaited<ReturnType<typeof buildFrontendDiagnosticsReadinessGate>>;
  decisionLog: Awaited<ReturnType<typeof buildFrontendDiagnosticsDecisionLog>>;
  handoffLabel: "proceed" | "stabilize" | "hold";
  proceedOrHoldSequence: string;
  notes: string[];
};

export async function buildFrontendDiagnosticsHandoffPacket(): Promise<FrontendDiagnosticsHandoffPacket> {
  const [latest, summary, compare, readiness, decisionLog] = await Promise.all([
    readLatestFrontendDiagnosticsHistoryEntry(),
    buildFrontendDiagnosticsSummary(),
    buildFrontendDiagnosticsCompare(),
    buildFrontendDiagnosticsReadinessGate(),
    buildFrontendDiagnosticsDecisionLog(),
  ]);

  const handoffLabel: FrontendDiagnosticsHandoffPacket["handoffLabel"] = readiness.decision.level === "go"
    ? "proceed"
    : readiness.decision.level === "conditional"
      ? "stabilize"
      : "hold";

  const notes = [
    `Latest posture is ${latest?.posture ?? "unknown"} in ${latest?.mode ?? "unknown"} mode.`,
    `Readiness decision is ${readiness.decision.level} and recovery posture is ${readiness.recovery.readiness.label}.`,
    `Decision log currently tracks ${decisionLog.summary.totalEntries} entries with ${decisionLog.summary.holdEntries} hold decisions and ${decisionLog.summary.stabilizeEntries} stabilize decisions.`,
    handoffLabel === "proceed"
      ? "Use this handoff packet to preserve the current go posture before running the full validation/build sequence."
      : handoffLabel === "stabilize"
        ? "Treat this handoff packet as a stabilization checkpoint; clear watch items before trusting the next build pass."
        : "Treat this handoff packet as a hold-state audit record and resolve blockers before proceeding.",
  ];

  return {
    generatedAt: new Date().toISOString(),
    packetId: `frontend-handoff-${Date.now()}`,
    latest,
    summary,
    compare,
    readiness,
    decisionLog,
    handoffLabel,
    proceedOrHoldSequence: decisionLog.proceedOrHoldSequence,
    notes,
  };
}
