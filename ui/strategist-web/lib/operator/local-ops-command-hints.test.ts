import { describe, expect, it } from "vitest";
import registryJson from "./local-ops-command-registry.json";
import {
  FIRST_RUN_CLI_COMMAND_IDS,
  FIRST_RUN_CLI_HINTS,
  LOCAL_OPS_COMMAND_REGISTRY,
  RELEASE_CONTROL_COMMAND_HINTS,
  RELEASE_CONTROL_COMMAND_IDS,
  localOpsCommandById,
  releaseControlCommandHintBlock,
} from "./local-ops-command-hints";

describe("local-ops-command-registry.json", () => {
  it("uses the expected schema and unique ids", () => {
    expect((registryJson as { schema_version: string }).schema_version).toBe("local_ops_command_registry/v1");
    const ids = LOCAL_OPS_COMMAND_REGISTRY.map((c) => c.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("exposes every release-control id", () => {
    for (const id of RELEASE_CONTROL_COMMAND_IDS) {
      expect(localOpsCommandById(id)?.commandText.length).toBeGreaterThan(3);
    }
    expect(releaseControlCommandHintBlock()).toContain("strategy-validator-release-candidate");
  });

  it("keeps RELEASE_CONTROL_COMMAND_HINTS keys aligned with registry text", () => {
    expect(RELEASE_CONTROL_COMMAND_HINTS.rcGenerate).toContain("strategy-validator-release-candidate generate");
    expect(RELEASE_CONTROL_COMMAND_HINTS.stEvidence).toContain("strategy-validator-single-tenant-evidence");
  });

  it("lists first-run hints in registry order", () => {
    expect(FIRST_RUN_CLI_HINTS).toHaveLength(FIRST_RUN_CLI_COMMAND_IDS.length);
    expect(FIRST_RUN_CLI_HINTS[0]?.command).toContain("strategy-validator-deployment-env-check");
  });

  it("does not embed obvious secret markers in command text", () => {
    for (const c of LOCAL_OPS_COMMAND_REGISTRY) {
      const t = c.commandText.toLowerCase();
      expect(t).not.toContain("bearer ");
      expect(t).not.toContain("x-strategy-validator-token");
      expect(t).not.toContain("password=");
    }
  });
});
