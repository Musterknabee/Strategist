export const runtime = "nodejs";
export const dynamic = "force-dynamic";

import { buildFrontendDiagnosticsRunbook } from "@/lib/server/diagnostics-runbook";
import { jsonNoStore } from "@/lib/server/response";

export async function GET() {
  const payload = await buildFrontendDiagnosticsRunbook();
  return jsonNoStore(payload);
}
