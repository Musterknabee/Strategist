export const runtime = "nodejs";
export const dynamic = "force-dynamic";

import { jsonNoStore } from "@/lib/server/response";
import { buildFrontendDiagnosticsCheckpointRegister } from "@/lib/server/diagnostics-checkpoint-register";

export async function GET() {
  const payload = await buildFrontendDiagnosticsCheckpointRegister();
  return jsonNoStore(payload);
}
