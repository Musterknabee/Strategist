export const runtime = "nodejs";
export const dynamic = "force-dynamic";

import { jsonNoStore } from "@/lib/server/response";
import { buildFrontendDiagnosticsIncidentPlaybook } from "@/lib/server/diagnostics-incident-playbook";

export async function GET() {
  const payload = await buildFrontendDiagnosticsIncidentPlaybook();
  return jsonNoStore(payload);
}
