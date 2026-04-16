import { NextRequest } from "next/server";

import { fetchPackDetail } from "@/lib/server/backend";
import { jsonNoStore } from "@/lib/server/response";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const payload = await fetchPackDetail({
    pack_kind: searchParams.get("pack_kind") ?? undefined,
    manifest_path: searchParams.get("manifest_path") ?? undefined,
  });
  return jsonNoStore(payload);
}
