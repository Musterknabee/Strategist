import { NextResponse } from "next/server";

import { buildFrontendDiagnosticsCompare } from "@/lib/server/diagnostics-compare";
import { jsonNoStore } from "@/lib/server/response";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const payload = await buildFrontendDiagnosticsCompare();
  return jsonNoStore(payload, { status: 200 });
}
