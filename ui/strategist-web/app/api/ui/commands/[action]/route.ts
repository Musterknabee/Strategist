import { NextRequest } from "next/server";

import { submitUiCommand } from "@/lib/server/backend";
import { jsonNoStore } from "@/lib/server/response";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: NextRequest, context: { params: Promise<{ action: string }> }) {
  const { action } = await context.params;
  const body = await request.json().catch(() => ({}));
  const payload = await submitUiCommand(action, body);
  return jsonNoStore(payload);
}
