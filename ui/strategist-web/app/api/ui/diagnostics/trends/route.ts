import { buildFrontendDiagnosticsTrends } from "@/lib/server/diagnostics-trends";
import { jsonNoStore } from "@/lib/server/response";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const windowSize = Number.parseInt(searchParams.get("window") ?? "30", 10);
  return jsonNoStore(await buildFrontendDiagnosticsTrends(Number.isFinite(windowSize) ? windowSize : 30));
}
