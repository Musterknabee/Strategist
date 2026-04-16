import { buildFrontendDiagnosticsActionQueue } from "@/lib/server/diagnostics-action-queue";
import { jsonNoStore } from "@/lib/server/response";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const payload = await buildFrontendDiagnosticsActionQueue();
  return jsonNoStore(payload);
}
