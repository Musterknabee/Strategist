import { buildFrontendDiagnosticsCertificationManifest } from "@/lib/server/diagnostics-certification-manifest";
import { buildFrontendDiagnosticsHandoffPacket } from "@/lib/server/diagnostics-handoff-packet";
import { buildFrontendDiagnosticsReadinessGate } from "@/lib/server/diagnostics-readiness-gate";
import { buildFrontendDiagnosticsDecisionLog } from "@/lib/server/diagnostics-decision-log";
import { buildFrontendDiagnosticsCheckpointRegister } from "@/lib/server/diagnostics-checkpoint-register";
import { readLatestFrontendDiagnosticsHistoryEntry } from "@/lib/server/diagnostics-history";

export type FrontendDiagnosticsReleaseCandidateDossier = {
  generatedAt: string;
  dossierId: string;
  latest: Awaited<ReturnType<typeof readLatestFrontendDiagnosticsHistoryEntry>>;
  readiness: Awaited<ReturnType<typeof buildFrontendDiagnosticsReadinessGate>>;
  decisionLog: Awaited<ReturnType<typeof buildFrontendDiagnosticsDecisionLog>>;
  handoff: Awaited<ReturnType<typeof buildFrontendDiagnosticsHandoffPacket>>;
  checkpointRegister: Awaited<ReturnType<typeof buildFrontendDiagnosticsCheckpointRegister>>;
  certification: Awaited<ReturnType<typeof buildFrontendDiagnosticsCertificationManifest>>;
  releaseLabel: "release-candidate" | "conditional-candidate" | "withhold-candidate";
  executiveSummary: string;
  releaseChecks: Array<{
    id: string;
    label: string;
    status: "ready" | "watch" | "blocked";
    detail: string;
    route: string;
    command?: string;
  }>;
  preReleaseSequence: string;
  notes: string[];
};

export async function buildFrontendDiagnosticsReleaseCandidateDossier(): Promise<FrontendDiagnosticsReleaseCandidateDossier> {
  const [latest, readiness, decisionLog, handoff, checkpointRegister, certification] = await Promise.all([
    readLatestFrontendDiagnosticsHistoryEntry(),
    buildFrontendDiagnosticsReadinessGate(),
    buildFrontendDiagnosticsDecisionLog(),
    buildFrontendDiagnosticsHandoffPacket(),
    buildFrontendDiagnosticsCheckpointRegister(),
    buildFrontendDiagnosticsCertificationManifest(),
  ]);

  const releaseChecks: FrontendDiagnosticsReleaseCandidateDossier["releaseChecks"] = [
    {
      id: "readiness",
      label: "Readiness gate",
      status: readiness.decision.level === "go" ? "ready" : readiness.decision.level === "conditional" ? "watch" : "blocked",
      detail: readiness.decision.rationale,
      route: "/settings/readiness-gate",
      command: readiness.proceedSequence,
    },
    {
      id: "certification",
      label: "Certification manifest",
      status: certification.certificationLevel === "certified" ? "ready" : certification.certificationLevel === "conditional" ? "watch" : "blocked",
      detail: certification.attestation,
      route: "/settings/certification-manifest",
      command: certification.finalizeSequence,
    },
    {
      id: "checkpoints",
      label: "Checkpoint register",
      status: checkpointRegister.checkpoints.some((item) => item.status === "blocked")
        ? "blocked"
        : checkpointRegister.checkpoints.some((item) => item.status === "watch")
          ? "watch"
          : "ready",
      detail: `Ready=${checkpointRegister.checkpoints.filter((item) => item.status === "ready").length}, Watch=${checkpointRegister.checkpoints.filter((item) => item.status === "watch").length}, Blocked=${checkpointRegister.checkpoints.filter((item) => item.status === "blocked").length}.`,
      route: "/settings/checkpoint-register",
      command: checkpointRegister.checkpointBeforeProceedSequence,
    },
    {
      id: "handoff",
      label: "Handoff packet",
      status: handoff.handoffLabel === "proceed" ? "ready" : handoff.handoffLabel === "stabilize" ? "watch" : "blocked",
      detail: `Current handoff label is ${handoff.handoffLabel}.`,
      route: "/settings/handoff-packet",
      command: handoff.proceedOrHoldSequence,
    },
  ];

  const releaseLabel: FrontendDiagnosticsReleaseCandidateDossier["releaseLabel"] = releaseChecks.some((item) => item.status === "blocked")
    ? "withhold-candidate"
    : releaseChecks.some((item) => item.status === "watch")
      ? "conditional-candidate"
      : "release-candidate";

  const executiveSummary = releaseLabel === "release-candidate"
    ? "Local frontend diagnostics support a release-candidate posture; continue with check/build while preserving the exported handoff trail."
    : releaseLabel === "conditional-candidate"
      ? "Local frontend diagnostics only support a conditional candidate posture; clear watch items before treating the shell as fully release-ready."
      : "Local frontend diagnostics do not support a release candidate yet; hold and stabilize before continuing.";

  const preReleaseSequence = [
    "npm run export:diagnostics",
    releaseLabel === "release-candidate" ? "npm run check" : "npm run recommend:diagnostics",
    releaseLabel === "release-candidate" ? "npm run build" : "npm run smoke",
    "npm run summarize:diagnostics",
  ].join(" && ");

  const notes = [
    `Latest posture is ${latest?.posture ?? "unknown"} in ${latest?.mode ?? "unknown"} mode.`,
    `Readiness is ${readiness.decision.level}; certification is ${certification.certificationLevel}; release label is ${releaseLabel}.`,
    releaseLabel === "release-candidate"
      ? "Use this dossier as the final local pre-release artifact before a fuller local build/test confirmation."
      : releaseLabel === "conditional-candidate"
        ? "Preserve this dossier and clear watch items before elevating the shell to a release-candidate posture."
        : "Treat this dossier as a hold artifact and stay in stabilize mode until blocked items are cleared.",
  ];

  return {
    generatedAt: new Date().toISOString(),
    dossierId: `frontend-rc-${Date.now()}`,
    latest,
    readiness,
    decisionLog,
    handoff,
    checkpointRegister,
    certification,
    releaseLabel,
    executiveSummary,
    releaseChecks,
    preReleaseSequence,
    notes,
  };
}
