export const runtime = "nodejs";
export const dynamic = "force-dynamic";

import { jsonNoStore } from "@/lib/server/response";
import { buildFrontendDiagnosticsReleaseCandidateDossier } from "@/lib/server/diagnostics-release-candidate-dossier";

export async function GET() {
  const payload = await buildFrontendDiagnosticsReleaseCandidateDossier();
  return jsonNoStore(payload);
}
