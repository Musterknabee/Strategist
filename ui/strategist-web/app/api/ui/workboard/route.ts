import { fetchWorkboard } from "@/lib/server/backend";
import { jsonNoStore } from "@/lib/server/response";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const payload = await fetchWorkboard();
  return jsonNoStore(payload);
}
