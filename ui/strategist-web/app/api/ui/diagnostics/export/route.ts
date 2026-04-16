import { NextResponse } from "next/server";

import { buildDiagnosticsExportSnapshot } from "@/lib/server/diagnostics-export";
import { jsonNoStore } from "@/lib/server/response";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const snapshot = await buildDiagnosticsExportSnapshot();
    return jsonNoStore(snapshot);
  } catch (error) {
    return NextResponse.json(
      {
        error: "Failed to build diagnostics export snapshot.",
        detail: error instanceof Error ? error.message : String(error),
      },
      {
        status: 500,
        headers: {
          "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
          Pragma: "no-cache",
          Expires: "0",
        },
      }
    );
  }
}
