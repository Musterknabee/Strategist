import { NextResponse } from "next/server";

import { buildFrontendDiagnosticsDecisionLog } from "@/lib/server/diagnostics-decision-log";
import { jsonNoStore } from "@/lib/server/response";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const payload = await buildFrontendDiagnosticsDecisionLog();
  return jsonNoStore(payload);
}
