import { buildFrontendDiagnosticsRecommendations } from "@/lib/server/diagnostics-recommendations";

export type FrontendDiagnosticsActionQueueItem = {
  id: string;
  title: string;
  priority: "high" | "medium" | "low";
  status: "queued" | "watch" | "later";
  rationale: string;
  command?: string;
  suggestedRoute?: string;
};

export type FrontendDiagnosticsActionQueue = {
  generatedAt: string;
  summary: {
    queued: number;
    watch: number;
    later: number;
    latestPosture: string;
    latestMode: string;
  };
  items: FrontendDiagnosticsActionQueueItem[];
  notes: string[];
};

function mapPriorityToStatus(priority: "high" | "medium" | "low"): FrontendDiagnosticsActionQueueItem["status"] {
  if (priority === "high") return "queued";
  if (priority === "medium") return "watch";
  return "later";
}

function suggestRouteForRecommendation(id: string): string | undefined {
  if (id.includes('compare')) return '/settings/compare';
  if (id.includes('warning') || id.includes('maintain')) return '/settings/status-board';
  if (id.includes('bootstrap') || id.includes('smoke')) return '/settings/quick-actions';
  if (id.includes('investigate')) return '/settings/latest';
  return '/settings/recommendations';
}

export async function buildFrontendDiagnosticsActionQueue(): Promise<FrontendDiagnosticsActionQueue> {
  const recommendations = await buildFrontendDiagnosticsRecommendations();
  const items: FrontendDiagnosticsActionQueueItem[] = recommendations.recommendations.map((rec) => ({
    id: rec.id,
    title: rec.title,
    priority: rec.priority,
    status: mapPriorityToStatus(rec.priority),
    rationale: rec.rationale,
    command: rec.command,
    suggestedRoute: suggestRouteForRecommendation(rec.id),
  }));

  const summary = {
    queued: items.filter((item) => item.status === 'queued').length,
    watch: items.filter((item) => item.status === 'watch').length,
    later: items.filter((item) => item.status === 'later').length,
    latestPosture: recommendations.latest?.posture ?? 'none',
    latestMode: recommendations.latest?.mode ?? 'none',
  };

  const notes = [
    summary.queued
      ? `Action queue contains ${summary.queued} queued items that should be handled before trusting the current frontend posture.`
      : 'No queued diagnostics actions are currently blocking local frontend trust posture.',
    summary.watch
      ? `${summary.watch} items are in watch posture and should be reviewed during the next validation cycle.`
      : 'No watch-posture diagnostics actions are currently pending.',
    'Use the recommendations page for rationale detail and the quick-actions/runbook pages for copy-ready command sequences.',
  ];

  return {
    generatedAt: new Date().toISOString(),
    summary,
    items,
    notes,
  };
}
