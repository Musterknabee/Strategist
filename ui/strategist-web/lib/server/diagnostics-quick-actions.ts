import { getFrontendDiagnosticsManifest, type DiagnosticsCommand } from "@/lib/diagnostics";
import { buildFrontendDiagnosticsSummary } from "@/lib/server/diagnostics-summary";

type QuickActionGroup = {
  id: string;
  label: string;
  description: string;
  commands: DiagnosticsCommand[];
};

export type FrontendDiagnosticsQuickActions = {
  generatedAt: string;
  summary: Awaited<ReturnType<typeof buildFrontendDiagnosticsSummary>>;
  groups: QuickActionGroup[];
};

function pickCommands(labels: string[]) {
  const manifest = getFrontendDiagnosticsManifest();
  return labels
    .map((label) => manifest.commands.find((command) => command.label === label))
    .filter((value): value is DiagnosticsCommand => Boolean(value));
}

export async function buildFrontendDiagnosticsQuickActions(): Promise<FrontendDiagnosticsQuickActions> {
  const summary = await buildFrontendDiagnosticsSummary();

  return {
    generatedAt: new Date().toISOString(),
    summary,
    groups: [
      {
        id: "bootstrap",
        label: "Bootstrap & inspect",
        description: "Get the local shell into a known state before opening the browser.",
        commands: pickCommands(["Bootstrap env", "Doctor", "Smoke"]),
      },
      {
        id: "verify",
        label: "Verify & build",
        description: "Run the light verification pass first, then escalate to build only when check is clean.",
        commands: pickCommands(["Check", "Build", "Validate"]),
      },
      {
        id: "diagnostics",
        label: "Diagnostics trail",
        description: "Create, summarize, prune, or reset local diagnostics artifacts between bring-up cycles.",
        commands: pickCommands([
          "Export diagnostics",
          "Summarize diagnostics",
          "Prune diagnostics history",
          "Reset diagnostics artifacts",
        ]),
      },
    ],
  };
}
