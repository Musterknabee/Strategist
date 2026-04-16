export const runtime = "nodejs";
export const dynamic = "force-dynamic";

import { jsonNoStore } from "@/lib/server/response";
import { buildFrontendDiagnosticsRecommendations } from "@/lib/server/diagnostics-recommendations";

export async function GET() {
  const payload = await buildFrontendDiagnosticsRecommendations();
  return jsonNoStore(payload);
}
