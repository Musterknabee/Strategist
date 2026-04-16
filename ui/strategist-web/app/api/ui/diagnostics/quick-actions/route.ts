export const runtime = "nodejs";
export const dynamic = "force-dynamic";

import { jsonNoStore } from "@/lib/server/response";
import { buildFrontendDiagnosticsQuickActions } from "@/lib/server/diagnostics-quick-actions";

export async function GET() {
  const payload = await buildFrontendDiagnosticsQuickActions();
  return jsonNoStore(payload);
}
