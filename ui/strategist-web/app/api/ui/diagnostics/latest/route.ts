import { NextResponse } from "next/server";

import { readLatestFrontendDiagnosticsHistoryEntry } from "@/lib/server/diagnostics-history";
import { jsonNoStore } from "@/lib/server/response";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const latest = await readLatestFrontendDiagnosticsHistoryEntry();
    return jsonNoStore({ generatedAt: new Date().toISOString(), latest });
  } catch (error) {
    return NextResponse.json(
      {
        error: "Failed to read latest diagnostics export history entry.",
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
