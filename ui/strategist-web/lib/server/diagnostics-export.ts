import { getFrontendDiagnosticsManifest } from "@/lib/diagnostics";
import { getFrontendEnvConfig } from "@/lib/env";
import { buildFrontendPreflightReport } from "@/lib/server/preflight";
import { fetchRuntime } from "@/lib/server/backend";
import type { FrontendPreflightCheck } from "@/lib/server/preflight";

export type DiagnosticsExportSnapshot = {
  exportId: string;
  generatedAt: string;
  mode: "mock-backed" | "backend-connected";
  env: ReturnType<typeof getFrontendEnvConfig>;
  manifest: ReturnType<typeof getFrontendDiagnosticsManifest>;
  runtime: Awaited<ReturnType<typeof fetchRuntime>>;
  preflight: Awaited<ReturnType<typeof buildFrontendPreflightReport>>;
  notes: string[];
  metadata: {
    routeCount: number;
    commandCount: number;
    probeCount: number;
    warningCount: number;
  };
};

export async function buildDiagnosticsExportSnapshot(): Promise<DiagnosticsExportSnapshot> {
  const env = getFrontendEnvConfig();
  const runtime = await fetchRuntime();
  const preflight = await buildFrontendPreflightReport();
  const mode = env.forceMocks || !env.backendBaseUrl ? "mock-backed" : "backend-connected";
  const manifest = getFrontendDiagnosticsManifest();
  const generatedAt = new Date().toISOString();

  return {
    exportId: `diag-${generatedAt.replace(/[:.]/g, "-")}`,
    generatedAt,
    mode,
    env,
    manifest,
    runtime,
    preflight,
    notes: [
      mode === "mock-backed"
        ? "Frontend is currently operating in mock-backed mode."
        : "Frontend is currently configured for backend-connected mode.",
      "Use this snapshot for local bring-up handoff or UI diagnostics review.",
      "This export is read-only and does not mutate backend state.",
    ],
    metadata: {
      routeCount: manifest.routes.length,
      commandCount: manifest.commands.length,
      probeCount: preflight.checks.length,
      warningCount: preflight.checks.filter((probe: FrontendPreflightCheck) => !probe.ok).length,
    },
  };
}
