import { buildFrontendDiagnosticsCompare } from "@/lib/server/diagnostics-compare";
import { readLatestFrontendDiagnosticsHistoryEntry } from "@/lib/server/diagnostics-history";
import { buildFrontendDiagnosticsStatusBoard } from "@/lib/server/diagnostics-status-board";
import { buildFrontendDiagnosticsSummary } from "@/lib/server/diagnostics-summary";

export type FrontendDiagnosticsRecommendation = {
  id: string;
  priority: "high" | "medium" | "low";
  title: string;
  rationale: string;
  command?: string;
};

export type FrontendDiagnosticsRecommendations = {
  generatedAt: string;
  latest: Awaited<ReturnType<typeof readLatestFrontendDiagnosticsHistoryEntry>>;
  summary: Awaited<ReturnType<typeof buildFrontendDiagnosticsSummary>>;
  compare: Awaited<ReturnType<typeof buildFrontendDiagnosticsCompare>>;
  board: Awaited<ReturnType<typeof buildFrontendDiagnosticsStatusBoard>>;
  recommendations: FrontendDiagnosticsRecommendation[];
};

export async function buildFrontendDiagnosticsRecommendations(): Promise<FrontendDiagnosticsRecommendations> {
  const [latest, summary, compare, board] = await Promise.all([
    readLatestFrontendDiagnosticsHistoryEntry(),
    buildFrontendDiagnosticsSummary(),
    buildFrontendDiagnosticsCompare(),
    buildFrontendDiagnosticsStatusBoard(),
  ]);

  const recommendations: FrontendDiagnosticsRecommendation[] = [];

  if (!latest) {
    recommendations.push(
      {
        id: "bootstrap-first-run",
        priority: "high",
        title: "Bootstrap and start the first local run",
        rationale:
          "No diagnostics history exists yet, so the settings center cannot compare the latest posture against a baseline.",
        command: "npm run bootstrap:env && npm install && npm run doctor && npm run dev",
      },
      {
        id: "smoke-and-export",
        priority: "high",
        title: "Run smoke checks and export the first diagnostics snapshot",
        rationale:
          "A first exported snapshot unlocks history, summary, compare, trends, and status-board surfaces.",
        command: "npm run smoke && npm run export:diagnostics && npm run summarize:diagnostics",
      }
    );
  } else {
    if (latest.posture !== "ok") {
      recommendations.push({
        id: "investigate-latest-posture",
        priority: "high",
        title: `Investigate latest posture: ${latest.posture}`,
        rationale:
          "The latest diagnostics run is not fully healthy. Review runtime, preflight, and history before trusting the current shell posture.",
        command: "npm run doctor && npm run smoke && npm run export:diagnostics",
      });
    }

    if (!compare.postureAligned || !compare.modeAligned) {
      recommendations.push({
        id: "compare-latest-vs-history",
        priority: "medium",
        title: "Compare the latest run against recent history",
        rationale:
          "The current run differs from the recent aggregate posture or mode, so it may not be representative of your normal local environment.",
        command: "npm run summarize:diagnostics && npm run export:diagnostics",
      });
    }

    if (summary.warningRuns > 0 || summary.attentionRuns > 0) {
      recommendations.push({
        id: "review-warning-pressure",
        priority: summary.attentionRuns > 0 ? "high" : "medium",
        title: "Review warning and attention pressure before pruning history",
        rationale:
          `Recent diagnostics history includes ${summary.warningRuns} warning runs and ${summary.attentionRuns} attention runs.`,
        command: "npm run summarize:diagnostics && npm run prune:diagnostics",
      });
    }

    recommendations.push({
      id: "maintain-diagnostics-loop",
      priority: "low",
      title: "Keep the recurring diagnostics loop current",
      rationale:
        "A fresh export and summary keep status-board, trends, and compare surfaces representative of your current shell posture.",
      command: board.maintenanceLoop,
    });
  }

  if (!recommendations.length) {
    recommendations.push({
      id: "continue-validation",
      priority: "low",
      title: "Continue with the full validation sequence",
      rationale:
        "Current diagnostics do not indicate an urgent issue. Continue through typecheck, test, and build for a fuller signal.",
      command: "npm run check && npm run build",
    });
  }

  return {
    generatedAt: new Date().toISOString(),
    latest,
    summary,
    compare,
    board,
    recommendations,
  };
}
