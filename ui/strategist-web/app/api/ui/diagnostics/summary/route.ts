export const runtime = "nodejs";
export const dynamic = "force-dynamic";

import { buildFrontendDiagnosticsSummary } from "@/lib/server/diagnostics-summary";
import { jsonNoStore } from "@/lib/server/response";

export async function GET() {
  const summary = await buildFrontendDiagnosticsSummary();
  return jsonNoStore(summary);
}
