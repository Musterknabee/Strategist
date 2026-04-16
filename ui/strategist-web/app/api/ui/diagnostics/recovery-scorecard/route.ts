import { NextResponse } from "next/server";

import { buildFrontendDiagnosticsRecoveryScorecard } from "@/lib/server/diagnostics-recovery-scorecard";
import { jsonNoStore } from "@/lib/server/response";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const payload = await buildFrontendDiagnosticsRecoveryScorecard();
  return jsonNoStore(payload);
}
