import { runFrontendPreflight } from "@/lib/server/preflight";
import { jsonNoStore } from "@/lib/server/response";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const report = await runFrontendPreflight();
  return jsonNoStore(report);
}
