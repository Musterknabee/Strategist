import { buildFrontendDiagnosticsCertificationManifest } from "@/lib/server/diagnostics-certification-manifest";
import { jsonNoStore } from "@/lib/server/response";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const payload = await buildFrontendDiagnosticsCertificationManifest();
  return jsonNoStore(payload);
}
