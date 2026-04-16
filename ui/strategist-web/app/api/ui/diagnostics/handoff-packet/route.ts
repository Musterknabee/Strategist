import { NextResponse } from "next/server";

import { buildFrontendDiagnosticsHandoffPacket } from "@/lib/server/diagnostics-handoff-packet";
import { jsonNoStore } from "@/lib/server/response";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const payload = await buildFrontendDiagnosticsHandoffPacket();
  return jsonNoStore(payload);
}
