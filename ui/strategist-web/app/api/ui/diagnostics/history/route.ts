import { NextRequest, NextResponse } from "next/server";

import { readFrontendDiagnosticsHistory } from "@/lib/server/diagnostics-history";
import { jsonNoStore } from "@/lib/server/response";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const limit = Number.parseInt(searchParams.get("limit") ?? "24", 10);
    const mode = searchParams.get("mode") ?? "all";
    const posture = searchParams.get("posture") ?? "all";
    const search = searchParams.get("search") ?? "";
    const history = await readFrontendDiagnosticsHistory({ limit, mode: mode as any, posture, search });
    return jsonNoStore({
      generatedAt: new Date().toISOString(),
      count: history.length,
      filters: { limit, mode, posture, search },
      history,
    });
  } catch (error) {
    return NextResponse.json(
      {
        error: "Failed to read diagnostics export history.",
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
