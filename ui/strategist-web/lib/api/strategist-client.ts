import { getPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { StrategistApiError } from "@/lib/api/strategist-errors";

function joinBaseAndPath(base: string, path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${base}${p}`;
}

function safeErrorDetail(text: string, maxLength: number): string {
  return text.slice(0, maxLength);
}

async function readJsonResponse<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch {
    throw new StrategistApiError("Response was not valid JSON", response.status);
  }
}

async function raiseForJsonResponse(response: Response, kindLabel: "read-plane" | "mutation"): Promise<void> {
  if (response.status === 401 || response.status === 403) {
    const text = await response.text();
    throw new StrategistApiError(
      `Not authorized for this ${kindLabel} request`,
      response.status,
      safeErrorDetail(text, 500),
      "unauthorized",
    );
  }

  if (response.status === 502 || response.status === 503 || response.status === 504) {
    const text = await response.text();
    throw new StrategistApiError(
      `Backend unavailable (HTTP ${response.status})`,
      response.status,
      safeErrorDetail(text, 200),
      "unavailable",
    );
  }

  if (!response.ok) {
    const text = await response.text();
    throw new StrategistApiError(
      `Request failed (HTTP ${response.status})`,
      response.status,
      safeErrorDetail(text, 500),
    );
  }
}

/**
 * GET JSON from the Strategist API (read-plane). No auth headers in this tranche.
 */
export async function strategistGetJson<T>(path: string): Promise<{ status: number; data: T }> {
  const base = getPublicStrategistApiBaseUrl();
  const url = joinBaseAndPath(base, path);
  let response: Response;
  try {
    response = await fetch(url, {
      method: "GET",
      cache: "no-store",
      headers: { accept: "application/json" },
    });
  } catch (cause) {
    const msg = cause instanceof Error ? cause.message : "Network error";
    throw new StrategistApiError(`Backend unreachable: ${msg}`, undefined, msg, "unavailable");
  }

  await raiseForJsonResponse(response, "read-plane");
  const data = await readJsonResponse<T>(response);
  return { status: response.status, data };
}

export type StrategistMutationOptions = {
  /** Browser-supplied token. Never read from NEXT_PUBLIC env or bundled configuration. */
  mutationToken?: string | null;
  /** Optional operator principal header, validated by the backend. */
  operatorId?: string | null;
};

/**
 * POST JSON to the Strategist mutation plane. Callers must explicitly supply any token at runtime.
 */
export async function strategistPostJson<TBody, TResponse>(
  path: string,
  body: TBody,
  options: StrategistMutationOptions = {},
): Promise<{ status: number; data: TResponse }> {
  const base = getPublicStrategistApiBaseUrl();
  const url = joinBaseAndPath(base, path);
  const headers: Record<string, string> = {
    accept: "application/json",
    "content-type": "application/json",
  };
  const token = options.mutationToken?.trim();
  if (token) {
    headers.authorization = `Bearer ${token}`;
  }
  const operatorId = options.operatorId?.trim();
  if (operatorId) {
    headers["x-strategy-validator-operator"] = operatorId;
  }

  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      cache: "no-store",
      headers,
      body: JSON.stringify(body),
    });
  } catch (cause) {
    const msg = cause instanceof Error ? cause.message : "Network error";
    throw new StrategistApiError(`Backend unreachable: ${msg}`, undefined, msg, "unavailable");
  }

  await raiseForJsonResponse(response, "mutation");
  const data = await readJsonResponse<TResponse>(response);
  return { status: response.status, data };
}

/**
 * GET JSON for probe-style endpoints (e.g. `/readyz`) that may return 503 with a JSON body.
 * Does not throw on non-2xx; throws only on network failure or if JSON is expected but invalid when body present.
 */
export async function strategistProbeGetJson<T>(path: string): Promise<{
  status: number;
  data: T | null;
  rawText: string;
}> {
  const base = getPublicStrategistApiBaseUrl();
  const url = joinBaseAndPath(base, path);
  let response: Response;
  try {
    response = await fetch(url, {
      method: "GET",
      cache: "no-store",
      headers: { accept: "application/json" },
    });
  } catch (cause) {
    const msg = cause instanceof Error ? cause.message : "Network error";
    throw new StrategistApiError(`Backend unreachable: ${msg}`, undefined, msg, "unavailable");
  }
  const rawText = await response.text();
  if (!rawText.trim()) {
    return { status: response.status, data: null, rawText: "" };
  }
  try {
    const data = JSON.parse(rawText) as T;
    return { status: response.status, data, rawText };
  } catch {
    throw new StrategistApiError("Response was not valid JSON", response.status, rawText.slice(0, 200));
  }
}
