export const runtime = "nodejs";
export const dynamic = "force-dynamic";

import { jsonNoStore } from "@/lib/server/response";
import { buildFrontendDiagnosticsIndex } from "@/lib/server/diagnostics-index";

export async function GET() {
  const payload = await buildFrontendDiagnosticsIndex();
  return jsonNoStore(payload);
}
