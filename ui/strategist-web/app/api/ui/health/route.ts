import { getBackendRuntimeConfig } from "@/lib/server/backend";
import { jsonNoStore } from "@/lib/server/response";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  return jsonNoStore({
    ok: true,
    runtime: getBackendRuntimeConfig(),
    generated_at: new Date().toISOString(),
  });
}
