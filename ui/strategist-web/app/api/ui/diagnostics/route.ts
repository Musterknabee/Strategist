import { NextResponse } from "next/server";

import { getFrontendDiagnosticsManifest } from "@/lib/diagnostics";
import { jsonNoStore } from "@/lib/server/response";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  return jsonNoStore(getFrontendDiagnosticsManifest());
}
