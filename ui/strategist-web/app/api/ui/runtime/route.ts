import { NextRequest } from "next/server";

import { fetchRuntime } from "@/lib/server/backend";
import { jsonNoStore } from "@/lib/server/response";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const role = request.nextUrl.searchParams.get("role") ?? undefined;
  const payload = await fetchRuntime(role);
  return jsonNoStore(payload);
}
