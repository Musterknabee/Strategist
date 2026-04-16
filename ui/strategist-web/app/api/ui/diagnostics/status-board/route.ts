export const runtime = "nodejs";
export const dynamic = "force-dynamic";

import { buildFrontendDiagnosticsStatusBoard } from "@/lib/server/diagnostics-status-board";
import { jsonNoStore } from "@/lib/server/response";

export async function GET() {
  const payload = await buildFrontendDiagnosticsStatusBoard();
  return jsonNoStore(payload);
}
