import { buildFrontendDiagnosticsQuickActions } from "@/lib/server/diagnostics-quick-actions";
import { buildFrontendDiagnosticsSummary } from "@/lib/server/diagnostics-summary";

export type DiagnosticsRunbookStep = {
  id: string;
  label: string;
  command: string;
  description: string;
};

export type DiagnosticsRunbookWorkflow = {
  id: string;
  label: string;
  description: string;
  steps: DiagnosticsRunbookStep[];
  combinedCommand: string;
};

export type FrontendDiagnosticsRunbook = {
  generatedAt: string;
  summary: Awaited<ReturnType<typeof buildFrontendDiagnosticsSummary>>;
  workflows: DiagnosticsRunbookWorkflow[];
  guidance: string[];
};

function flattenCommands(groups: Awaited<ReturnType<typeof buildFrontendDiagnosticsQuickActions>>["groups"]) {
  return Object.fromEntries(groups.flatMap((group) => group.commands.map((command) => [command.label, command])));
}

function buildWorkflow(
  id: string,
  label: string,
  description: string,
  commandLabels: string[],
  commandMap: Record<string, { label: string; command: string; description: string }>,
): DiagnosticsRunbookWorkflow {
  const steps = commandLabels
    .map((commandLabel, index) => {
      const command = commandMap[commandLabel];
      if (!command) {
        return null;
      }
      return {
        id: `${id}-${index + 1}`,
        label: command.label,
        command: command.command,
        description: command.description,
      };
    })
    .filter((value): value is DiagnosticsRunbookStep => Boolean(value));

  return {
    id,
    label,
    description,
    steps,
    combinedCommand: steps.map((step) => step.command).join(" && "),
  };
}

export async function buildFrontendDiagnosticsRunbook(): Promise<FrontendDiagnosticsRunbook> {
  const summary = await buildFrontendDiagnosticsSummary();
  const quickActions = await buildFrontendDiagnosticsQuickActions();
  const commandMap = flattenCommands(quickActions.groups);

  return {
    generatedAt: new Date().toISOString(),
    summary,
    workflows: [
      buildWorkflow(
        "first-run",
        "First local run",
        "Bootstrap the env, inspect posture, start the shell, then smoke-check the representative BFF routes.",
        ["Bootstrap env", "Doctor", "Smoke"],
        commandMap,
      ),
      buildWorkflow(
        "verify-before-build",
        "Verify before build",
        "Run the light validation pass before attempting the full production build.",
        ["Check", "Build"],
        commandMap,
      ),
      buildWorkflow(
        "diagnostics-cycle",
        "Diagnostics maintenance cycle",
        "Export a fresh snapshot, summarize the trail, prune old rows, and reset when you want a clean restart.",
        ["Export diagnostics", "Summarize diagnostics", "Prune diagnostics history", "Reset diagnostics artifacts"],
        commandMap,
      ),
    ],
    guidance: [
      "Use the combined workflow command when you want a copy/paste-ready sequence rather than running each step manually.",
      "Use the first local run workflow after changing backend URL or force-mocks posture.",
      "Use the verify before build workflow before handing the frontend to someone else for review.",
      "Use the diagnostics maintenance cycle when repeated bring-up passes leave too much local history behind.",
    ],
  };
}
