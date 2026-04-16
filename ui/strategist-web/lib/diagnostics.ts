export type DiagnosticsRouteLink = {
  href: string;
  label: string;
  description: string;
};

export type DiagnosticsCommand = {
  label: string;
  command: string;
  description: string;
};

export type FrontendDiagnosticsManifest = {
  generatedAt: string;
  routes: DiagnosticsRouteLink[];
  commands: DiagnosticsCommand[];
  guidance: string[];
};

export function getFrontendDiagnosticsManifest(): FrontendDiagnosticsManifest {
  return {
    generatedAt: new Date().toISOString(),
    routes: [
      {
        href: "/settings",
        label: "Settings overview",
        description: "Entry point for local bring-up guidance and diagnostics navigation.",
      },
      {
        href: "/settings/runtime",
        label: "Runtime diagnostics",
        description: "Inspect normalized backend URL, timeout posture, and mock fallback mode.",
      },
      {
        href: "/settings/preflight",
        label: "Frontend preflight",
        description: "Probe representative BFF payloads before a full check/build pass.",
      },
      {
        href: "/settings/checklist",
        label: "Setup checklist",
        description: "Copy-friendly command sequence for local UI bring-up and validation.",
      },
      {
        href: "/settings/quick-actions",
        label: "Diagnostics quick actions",
        description: "Copy/paste-ready local command blocks grouped by bootstrap, verification, and diagnostics trail work.",
      },
      {
        href: "/settings/runbook",
        label: "Diagnostics runbook",
        description: "Combined workflow sequences for first local run, verify-before-build, and diagnostics maintenance.",
      },
      {
        href: "/settings/export",
        label: "Diagnostics export",
        description: "Single-snapshot export view for runtime posture and preflight results.",
      },
      {
        href: "/settings/history",
        label: "Diagnostics history",
        description: "Recent local diagnostics export history for repeated bring-up and review cycles.",
      },
      {
        href: "/settings/latest",
        label: "Latest diagnostics snapshot",
        description: "Quick view of the most recent local diagnostics export entry.",
      },
      {
        href: "/settings/summary",
        label: "Diagnostics summary",
        description: "Aggregate counts and posture trends over the local diagnostics history trail.",
      },
      {
        href: "/settings/trends",
        label: "Diagnostics trends",
        description: "Daily trend buckets for posture and backend/mock mode across recent local diagnostics history.",
      },
      {
        href: "/settings/compare",
        label: "Latest vs summary",
        description: "Compare the most recent diagnostics snapshot against the aggregate history summary.",
      },
      {
        href: "/settings/status-board",
        label: "Diagnostics status board",
        description: "Operational status board combining latest posture, aggregate summary, comparison, trends, and a recurring maintenance loop.",
      },
      {
        href: "/settings/recommendations",
        label: "Diagnostics recommendations",
        description: "Prioritized next moves derived from latest posture, aggregate history, compare alignment, and the diagnostics status board.",
      },
      {
        href: "/settings/escalation-matrix",
        label: "Diagnostics escalation matrix",
        description: "Escalation-oriented guidance for deciding when to monitor, stabilize, investigate, or reset the local diagnostics trail.",
      },
      {
        href: "/settings/action-queue",
        label: "Diagnostics action queue",
        description: "Queued, watch, and later actions derived from diagnostics recommendations so the next moves can be reviewed as an operational backlog.",
      },
      {
        href: "/settings/incident-playbook",
        label: "Diagnostics incident playbook",
        description: "Response-oriented local playbook for working escalation, action queue, and stabilization/reset loops.",
      },
      {
        href: "/settings/recovery-scorecard",
        label: "Diagnostics recovery scorecard",
        description: "Recovery-oriented scorecard for deciding whether the local shell is ready, still stabilizing, or blocked before a fuller validation pass.",
      },
      {
        href: "/settings/readiness-gate",
        label: "Diagnostics readiness gate",
        description: "Go / no-go view combining latest posture, blockers, recovery readiness, and a proceed sequence before a fuller validation pass.",
      },
      {
        href: "/settings/decision-log",
        label: "Diagnostics decision log",
        description: "Audit-style log of proceed / conditional / hold / stabilize decisions derived from readiness, recovery, and action-queue posture.",
      },
      {
        href: "/settings/handoff-packet",
        label: "Diagnostics handoff packet",
        description: "Aggregated proceed / stabilize / hold packet derived from latest posture, readiness gate, compare pressure, and the decision log.",
      },
      {
        href: "/settings/checkpoint-register",
        label: "Checkpoint register",
        description: "Final checkpoint list for deciding whether the local frontend is ready to proceed, should stay under watch, or should hold.",
      },
      {
        href: "/settings/release-candidate-dossier",
        label: "Release-candidate dossier",
        description: "Final pre-release dossier derived from readiness, certification, checkpoints, handoff, and decision posture.",
      },
      {
        href: "/settings/certification-manifest",
        label: "Certification manifest",
        description: "Final local certification and attestation derived from readiness, decision posture, handoff, and checkpoint alignment.",
      },
      {
        href: "/api/ui/diagnostics/history",
        label: "Diagnostics history API",
        description: "Recent local diagnostics exports written by the local export script.",
      },
      {
        href: "/api/ui/diagnostics/latest",
        label: "Latest diagnostics API",
        description: "Most recent local diagnostics export entry for quick bring-up checks.",
      },
      {
        href: "/api/ui/diagnostics/quick-actions",
        label: "Diagnostics quick-actions API",
        description: "Grouped copy/paste-ready command sets for local bring-up and diagnostics maintenance.",
      },
      {
        href: "/api/ui/diagnostics/runbook",
        label: "Diagnostics runbook API",
        description: "Combined workflow sequences for first-run bring-up, verify-before-build, and diagnostics maintenance.",
      },
      {
        href: "/api/ui/diagnostics/summary",
        label: "Diagnostics summary API",
        description: "Aggregate posture and mode counts computed from local diagnostics history.",
      },
      {
        href: "/api/ui/diagnostics/compare",
        label: "Diagnostics compare API",
        description: "Compare the most recent diagnostics export against the aggregate summary derived from local history.",
      },
      {
        href: "/api/ui/diagnostics/trends",
        label: "Diagnostics trends API",
        description: "Daily trend buckets for posture and backend/mock mode across recent local diagnostics history.",
      },
      {
        href: "/api/ui/diagnostics/index",
        label: "Diagnostics index API",
        description: "Combined manifest, summary, latest snapshot, and recommended validation sequence for the diagnostics center.",
      },
      {
        href: "/api/ui/diagnostics/status-board",
        label: "Diagnostics status-board API",
        description: "Combined latest, summary, compare, trends, and maintenance-loop view for the diagnostics center.",
      },
      {
        href: "/api/ui/diagnostics/recommendations",
        label: "Diagnostics recommendations API",
        description: "Prioritized next actions derived from latest posture, summary pressure, compare alignment, and status-board context.",
      },
      {
        href: "/api/ui/diagnostics/escalation-matrix",
        label: "Diagnostics escalation-matrix API",
        description: "Escalation-oriented rules and current posture for deciding when to monitor, stabilize, investigate, or reset the local diagnostics trail.",
      },
      {
        href: "/api/ui/diagnostics/action-queue",
        label: "Diagnostics action-queue API",
        description: "Queued, watch, and later actions derived from recommendations for a more operational diagnostics backlog view.",
      },
      {
        href: "/api/ui/diagnostics/incident-playbook",
        label: "Diagnostics incident-playbook API",
        description: "Response-oriented playbook tying escalation level, action queue posture, and stabilization/reset loops into one diagnostics view.",
      },
      {
        href: "/api/ui/diagnostics/recovery-scorecard",
        label: "Diagnostics recovery-scorecard API",
        description: "Recovery-oriented scorecard for deciding whether the local shell is ready, stabilizing, or blocked before a fuller validation pass.",
      },
      {
        href: "/api/ui/diagnostics/readiness-gate",
        label: "Diagnostics readiness-gate API",
        description: "Go / no-go diagnostics view combining latest posture, blockers, recovery readiness, and a proceed sequence before a fuller validation pass.",
      },
      {
        href: "/api/ui/diagnostics/decision-log",
        label: "Diagnostics decision-log API",
        description: "Audit-style diagnostics decision log derived from readiness, recovery, and action-queue posture.",
      },
      {
        href: "/api/ui/diagnostics/handoff-packet",
        label: "Diagnostics handoff-packet API",
        description: "Aggregated proceed / stabilize / hold handoff packet derived from latest posture, readiness gate, summary pressure, and the decision log.",
      },
      {
        href: "/api/ui/diagnostics/checkpoint-register",
        label: "Diagnostics checkpoint-register API",
        description: "Final checkpoint list derived from latest posture, readiness gate, handoff packet, decision log, and aggregate history pressure.",
      },
      {
        href: "/api/ui/diagnostics/release-candidate-dossier",
        label: "Release-candidate dossier API",
        description: "Final pre-release dossier combining readiness, certification, checkpoint, handoff, and decision posture for the local shell.",
      },
      {
        href: "/api/ui/diagnostics/certification-manifest",
        label: "Diagnostics certification-manifest API",
        description: "Final local certification and attestation derived from readiness, decision posture, handoff packet, and checkpoint alignment.",
      },
    ],
    commands: [
      {
        label: "Bootstrap env",
        command: "npm run bootstrap:env",
        description: "Create .env.local from .env.example when it does not exist yet.",
      },
      {
        label: "Doctor",
        command: "npm run doctor",
        description: "Validate local env posture and print the recommended next steps.",
      },
      {
        label: "Smoke",
        command: "npm run smoke",
        description: "Probe representative local BFF routes after starting the dev server.",
      },
      {
        label: "Check",
        command: "npm run check",
        description: "Run TypeScript and Vitest validation before building.",
      },
      {
        label: "Build",
        command: "npm run build",
        description: "Run a production Next.js build after the check step passes.",
      },
      {
        label: "Export diagnostics",
        command: "npm run export:diagnostics",
        description: "Write a local frontend diagnostics snapshot for handoff or review.",
      },
      {
        label: "Prune diagnostics history",
        command: "npm run prune:diagnostics",
        description: "Trim local diagnostics history to a manageable number of recent runs.",
      },
      {
        label: "Reset diagnostics artifacts",
        command: "npm run reset:diagnostics",
        description: "Remove the local diagnostics snapshot and history files for a clean restart.",
      },
      {
        label: "Summarize diagnostics",
        command: "npm run summarize:diagnostics",
        description: "Print a compact summary of the local diagnostics history trail.",
      },
      {
        label: "Recommend diagnostics next steps",
        command: "npm run recommend:diagnostics",
        description: "Print prioritized next moves based on the latest diagnostics history posture.",
      },
      {
        label: "Validate",
        command: "npm run validate",
        description: "Full local validation: typecheck, tests, then build.",
      },
    ],
    guidance: [
      "Use STRATEGIST_FORCE_MOCKS=true when you want a stable frontend-only demo or isolated UI work.",
      "Use /settings/runtime first if you are unsure which backend URL or timeout the web shell is actually using.",
      "Use /settings/preflight before a full build when you want a cheap signal on representative BFF routes.",
      "Use npm run smoke after npm run dev starts when you want a fast endpoint-level sanity check of the local shell.",
      "Use /settings/export or npm run export:diagnostics when you want a single diagnostics snapshot for handoff.",
      "Use /settings/history or npm run prune:diagnostics when repeated bring-up runs start to accumulate.",
      "Use /settings/latest when you only need the most recent posture instead of the full history.",
      "Use /settings/summary or npm run summarize:diagnostics when you want a compact aggregate view across recent runs.",
      "Use /settings/trends when you want a day-bucket view of whether warnings are isolated or recurring.",
      "Use /settings/status-board when you want one operational view that combines latest posture, summary pressure, compare alignment, and the recurring maintenance loop.",
      "Use /settings/recommendations or npm run recommend:diagnostics when you want prioritized next steps instead of only raw diagnostics pages.",
      "Use /settings/action-queue when you want the recommendation set grouped as an operational backlog with queued/watch/later posture.",
      "Use /settings/decision-log when you want an audit-style record of whether the current diagnostics posture says proceed, hold, or stabilize before a fuller validation pass.",
      "Use /settings/escalation-matrix when you want a higher-level decision aid for monitor/stabilize/investigate/reset posture.",
      "Use npm run reset:diagnostics when you want to clear local diagnostics artifacts and restart the trail cleanly.",
    ],
  };
}
