/**
 * Central registry for cockpit copyable CLI hints. Source of truth: `local-ops-command-registry.json`
 * (validated by `scripts/repository_truth_check.py`). The browser never executes these strings.
 */
import registryJson from "./local-ops-command-registry.json";

export type LocalOpsSafetyClass = "READ_ONLY" | "LOCAL_OPERATOR_ACTION" | "PRODUCTION_SENSITIVE" | "AUTH_REQUIRED";

export type LocalOpsCommandEntry = {
  id: string;
  label: string;
  commandText: string;
  safetyClass: LocalOpsSafetyClass;
  expectedEvidence: string;
  cockpitPane: string;
  docPath: string;
  productionWarning: string | null;
  primaryConsoleScript: string;
  pythonScriptPaths: string[];
  ciTruthGate: string;
};

type RegistryFile = {
  schema_version: string;
  commands: LocalOpsCommandEntry[];
};

const registry = registryJson as RegistryFile;

if (registry.schema_version !== "local_ops_command_registry/v1") {
  throw new Error(`local-ops-command-registry: unexpected schema_version ${registry.schema_version}`);
}

const byId: ReadonlyMap<string, LocalOpsCommandEntry> = new Map(registry.commands.map((c) => [c.id, c]));

export const LOCAL_OPS_COMMAND_REGISTRY: readonly LocalOpsCommandEntry[] = registry.commands;

export function localOpsCommandById(id: string): LocalOpsCommandEntry | undefined {
  return byId.get(id);
}

function requireCommand(id: string): LocalOpsCommandEntry {
  const c = byId.get(id);
  if (!c) throw new Error(`local-ops-command-registry: missing command id ${id}`);
  return c;
}

/** Ordered ids rendered in Release control pane (matches prior RELEASE_CONTROL_COMMAND_HINTS block). */
export const RELEASE_CONTROL_COMMAND_IDS = [
  "loc_rc_generate",
  "loc_rc_assess",
  "loc_rc_verify_bundle",
  "loc_st_evidence_final",
  "loc_st_acceptance",
  "loc_st_api_smoke_placeholder",
  "loc_package_repo_check",
  "loc_verify_repo_archive",
  "loc_research_os_release_readiness",
  "loc_research_os_handoff_build",
  "loc_research_os_handoff_signoff_verify",
  "loc_research_os_review_journal",
] as const;

/** Legacy keyed object for release-control-model primary hints and tests. */
export const RELEASE_CONTROL_COMMAND_HINTS = {
  rcGenerate: requireCommand("loc_rc_generate").commandText,
  rcAssess: requireCommand("loc_rc_assess").commandText,
  rcVerifyBundle: requireCommand("loc_rc_verify_bundle").commandText,
  stEvidence: requireCommand("loc_st_evidence_final").commandText,
  stAcceptance: requireCommand("loc_st_acceptance").commandText,
  stApiSmoke: requireCommand("loc_st_api_smoke_placeholder").commandText,
  pkgRepoCheck: requireCommand("loc_package_repo_check").commandText,
  verifyArchive: requireCommand("loc_verify_repo_archive").commandText,
  researchOsReleaseReadiness: requireCommand("loc_research_os_release_readiness").commandText,
  researchOsHandoff: requireCommand("loc_research_os_handoff_build").commandText,
  researchOsHandoffSignoffVerify: requireCommand("loc_research_os_handoff_signoff_verify").commandText,
  researchOsReviewJournal: requireCommand("loc_research_os_review_journal").commandText,
} as const;

export function releaseControlCommandHintBlock(): string {
  return RELEASE_CONTROL_COMMAND_IDS.map((id) => requireCommand(id).commandText).join("\n");
}

/** First-run wizard copy list — order matches checklist HINT_* indices. */
export const FIRST_RUN_CLI_COMMAND_IDS = [
  "loc_deployment_env_check",
  "loc_migrate",
  "loc_st_preflight_prepare",
  "loc_st_api_smoke_local",
  "loc_st_evidence_require_pass",
] as const;

export const FIRST_RUN_CLI_HINTS: { label: string; command: string }[] = FIRST_RUN_CLI_COMMAND_IDS.map((id) => {
  const c = requireCommand(id);
  return { label: c.label, command: c.commandText };
});

/** Index alignment with first-run-deployment-checklist HINT_* constants. */
export const FIRST_RUN_HINT_ENV = 0;
export const FIRST_RUN_HINT_MIGRATE = 1;
export const FIRST_RUN_HINT_PREFLIGHT = 2;
export const FIRST_RUN_HINT_SMOKE = 3;
export const FIRST_RUN_HINT_EVIDENCE = 4;
