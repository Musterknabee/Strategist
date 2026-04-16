import { fetchTribunal } from "@/lib/server/backend";
import { jsonNoStore } from "@/lib/server/response";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const data = await fetchTribunal();
  return jsonNoStore(data);
}
