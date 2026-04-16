import { buildFrontendDiagnosticsReadinessGate } from "@/lib/server/diagnostics-readiness-gate";
import { buildFrontendDiagnosticsDecisionLog } from "@/lib/server/diagnostics-decision-log";
import { buildFrontendDiagnosticsHandoffPacket } from "@/lib/server/diagnostics-handoff-packet";
import { buildFrontendDiagnosticsCheckpointRegister } from "@/lib/server/diagnostics-checkpoint-register";
import { readLatestFrontendDiagnosticsHistoryEntry } from "@/lib/server/diagnostics-history";

export type FrontendDiagnosticsCertificationManifest = {
  generatedAt: string;
  certificationId: string;
  latest: Awaited<ReturnType<typeof readLatestFrontendDiagnosticsHistoryEntry>>;
  readiness: Awaited<ReturnType<typeof buildFrontendDiagnosticsReadinessGate>>;
  decisionLog: Awaited<ReturnType<typeof buildFrontendDiagnosticsDecisionLog>>;
  handoff: Awaited<ReturnType<typeof buildFrontendDiagnosticsHandoffPacket>>;
  checkpointRegister: Awaited<ReturnType<typeof buildFrontendDiagnosticsCheckpointRegister>>;
  certificationLevel: "certified" | "conditional" | "withhold";
  attestation: string;
  certificationChecks: Array<{
    id: string;
    label: string;
    status: "pass" | "watch" | "fail";
    detail: string;
    route: string;
    command?: string;
  }>;
  finalizeSequence: string;
  notes: string[];
};

export async function buildFrontendDiagnosticsCertificationManifest(): Promise<FrontendDiagnosticsCertificationManifest> {
  const [latest, readiness, decisionLog, handoff, checkpointRegister] = await Promise.all([
    readLatestFrontendDiagnosticsHistoryEntry(),
    buildFrontendDiagnosticsReadinessGate(),
    buildFrontendDiagnosticsDecisionLog(),
    buildFrontendDiagnosticsHandoffPacket(),
    buildFrontendDiagnosticsCheckpointRegister(),
  ]);

  const certificationChecks: FrontendDiagnosticsCertificationManifest["certificationChecks"] = [
    {
      id: "readiness-gate",
      label: "Readiness gate",
      status: readiness.decision.level === "go" ? "pass" : readiness.decision.level === "conditional" ? "watch" : "fail",
      detail: readiness.decision.rationale,
      route: "/settings/readiness-gate",
      command: readiness.proceedSequence,
    },
    {
      id: "decision-log",
      label: "Decision posture",
      status: decisionLog.summary.holdEntries > 0 ? "fail" : decisionLog.summary.stabilizeEntries > 0 ? "watch" : "pass",
      detail: `Proceed=${decisionLog.summary.proceedEntries}, Hold=${decisionLog.summary.holdEntries}, Stabilize=${decisionLog.summary.stabilizeEntries}.`,
      route: "/settings/decision-log",
      command: decisionLog.proceedOrHoldSequence,
    },
    {
      id: "handoff-packet",
      label: "Handoff packet",
      status: handoff.handoffLabel === "proceed" ? "pass" : handoff.handoffLabel === "stabilize" ? "watch" : "fail",
      detail: `Current handoff label is ${handoff.handoffLabel}.`,
      route: "/settings/handoff-packet",
      command: handoff.proceedOrHoldSequence,
    },
    {
      id: "checkpoint-register",
      label: "Checkpoint register",
      status: checkpointRegister.checkpoints.some((item) => item.status === "blocked")
        ? "fail"
        : checkpointRegister.checkpoints.some((item) => item.status === "watch")
          ? "watch"
          : "pass",
      detail: `Ready=${checkpointRegister.checkpoints.filter((item) => item.status === "ready").length}, Watch=${checkpointRegister.checkpoints.filter((item) => item.status === "watch").length}, Blocked=${checkpointRegister.checkpoints.filter((item) => item.status === "blocked").length}.`,
      route: "/settings/checkpoint-register",
      command: checkpointRegister.checkpointBeforeProceedSequence,
    },
  ];

  const certificationLevel: FrontendDiagnosticsCertificationManifest["certificationLevel"] = certificationChecks.some((item) => item.status === "fail")
    ? "withhold"
    : certificationChecks.some((item) => item.status === "watch")
      ? "conditional"
      : "certified";

  const attestation = certificationLevel === "certified"
    ? "Frontend diagnostics are certified for proceed posture based on readiness, decision-log, handoff, and checkpoint alignment."
    : certificationLevel === "conditional"
      ? "Frontend diagnostics are only conditionally certified; preserve artifacts and clear watch items before trusting a full proceed posture."
      : "Frontend diagnostics certification is withheld until blocking posture is cleared across readiness, decision, handoff, and checkpoints.";

  const notes = [
    `Latest posture is ${latest?.posture ?? "unknown"} in ${latest?.mode ?? "unknown"} mode.`,
    `Readiness decision is ${readiness.decision.level}; certification level is ${certificationLevel}.`,
    certificationLevel === "certified"
      ? "You can use this manifest as the final local go/no-go attestation before a full validation/build pass."
      : certificationLevel === "conditional"
        ? "Treat this manifest as a conditional attestation and preserve export/history artifacts before proceeding."
        : "Treat this manifest as a no-go attestation and keep the shell in stabilize/hold mode.",
  ];

  return {
    generatedAt: new Date().toISOString(),
    certificationId: `frontend-cert-${Date.now()}`,
    latest,
    readiness,
    decisionLog,
    handoff,
    checkpointRegister,
    certificationLevel,
    attestation,
    certificationChecks,
    finalizeSequence: [
      "npm run export:diagnostics",
      "npm run summarize:diagnostics",
      certificationLevel === "certified" ? "npm run check" : "npm run recommend:diagnostics",
      certificationLevel === "certified" ? "npm run build" : "npm run smoke",
    ].join(" && "),
    notes,
  };
}
