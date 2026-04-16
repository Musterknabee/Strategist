import { buildFrontendDiagnosticsEscalationMatrix } from "@/lib/server/diagnostics-escalation-matrix";
import { jsonNoStore } from "@/lib/server/response";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const payload = await buildFrontendDiagnosticsEscalationMatrix();
  return jsonNoStore(payload);
}
