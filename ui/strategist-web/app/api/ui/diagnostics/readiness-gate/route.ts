export const runtime = "nodejs";
export const dynamic = "force-dynamic";

import { jsonNoStore } from "@/lib/server/response";
import { buildFrontendDiagnosticsReadinessGate } from "@/lib/server/diagnostics-readiness-gate";

export async function GET() {
  const payload = await buildFrontendDiagnosticsReadinessGate();
  return jsonNoStore(payload);
}
