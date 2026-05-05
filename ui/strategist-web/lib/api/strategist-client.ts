import { StrategistApiError } from "@/lib/api/strategist-errors";
import {
  getPublicStrategistApiBaseUrl,
  isStrategistDemoModeEnabled,
  tryGetPublicStrategistApiBaseUrl,
} from "@/lib/config/public-config";
import { getDemoReadPlanePayload } from "@/lib/demo/demo-mode";

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

function parseFastApiDetail(text: string): string | undefined {
  const t = text.trim();
  if (!t.startsWith("{")) return undefined;
  try {
    const j = JSON.parse(t) as { detail?: unknown };
    if (typeof j.detail === "string") return j.detail;
    if (Array.isArray(j.detail) && j.detail.length && typeof j.detail[0] === "object" && j.detail[0] !== null) {
      const msg = (j.detail[0] as { msg?: string }).msg;
      if (typeof msg === "string") return msg;
    }
  } catch {
    /* ignore */
  }
  return undefined;
}

async function raiseForJsonResponse(response: Response, kindLabel: "read-plane" | "mutation"): Promise<void> {
  if (response.status === 401 || response.status === 403) {
    const text = await response.text();
    const apiDetail = parseFastApiDetail(text);
    const label =
      response.status === 401
        ? "Mutation rejected (not authorized)"
        : "Mutation rejected (forbidden by server policy)";
    throw new StrategistApiError(
      apiDetail ? `${label}: ${apiDetail}` : `Not authorized for this ${kindLabel} request`,
      response.status,
      safeErrorDetail(text, 500),
      "unauthorized",
    );
  }

  if (response.status === 502 || response.status === 503 || response.status === 504) {
    const text = await response.text();
    const apiDetail = parseFastApiDetail(text);
    throw new StrategistApiError(
      apiDetail
        ? `Backend unavailable (HTTP ${response.status}): ${apiDetail}`
        : `Backend unavailable (HTTP ${response.status})`,
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

function demoFallback<T>(path: string): { status: number; data: T } | null {
  const demoPayload = isStrategistDemoModeEnabled() ? getDemoReadPlanePayload(path) : null;
  if (!demoPayload) return null;
  return { status: path === "/readyz" ? 503 : 299, data: demoPayload as T };
}

/**
 * GET JSON from the Strategist API (read-plane). No auth headers in this tranche.
 */
export async function strategistGetJson<T>(path: string): Promise<{ status: number; data: T }> {
  const baseResult = tryGetPublicStrategistApiBaseUrl();
  if (!baseResult.ok) {
    const demo = demoFallback<T>(path);
    if (demo) return demo;
    throw baseResult.error;
  }
  const base = baseResult.baseUrl;
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
    const demo = demoFallback<T>(path);
    if (demo) return demo;
    throw new StrategistApiError(`Backend unreachable: ${msg}`, undefined, msg, "unavailable");
  }

  await raiseForJsonResponse(response, "read-plane");
  const data = await readJsonResponse<T>(response);
  return { status: response.status, data };
}

export type StrategistMutationTokenDelivery = "authorization_bearer" | "x_strategy_validator_token";

export type StrategistMutationOptions = {
  /** Browser-supplied token. Never read from NEXT_PUBLIC env or bundled configuration. */
  mutationToken?: string | null;
  /** Optional operator principal header, validated by the backend. */
  operatorId?: string | null;
  /**
   * Default sends `Authorization: Bearer <token>`.
   * `x_strategy_validator_token` sends `X-Strategy-Validator-Token` (backend accepts either).
   */
  tokenDelivery?: StrategistMutationTokenDelivery;
};

/**
 * POST JSON to the Strategist mutation plane. Callers must explicitly supply any token at runtime.
 */
export async function strategistPostJson<TBody, TResponse>(
  path: string,
  body: TBody,
  options: StrategistMutationOptions = {},
): Promise<{ status: number; data: TResponse }> {
  if (isStrategistDemoModeEnabled()) {
    throw new StrategistApiError(
      "Demo mode disables mutation requests; no synthetic mutation success is allowed",
      undefined,
      "DEMO_MODE_MUTATION_DISABLED",
      "unauthorized",
    );
  }
  const base = getPublicStrategistApiBaseUrl();
  const url = joinBaseAndPath(base, path);
  const headers: Record<string, string> = {
    accept: "application/json",
    "content-type": "application/json",
  };
  const token = options.mutationToken?.trim();
  if (token) {
    if (options.tokenDelivery === "x_strategy_validator_token") {
      headers["x-strategy-validator-token"] = token;
    } else {
      headers.authorization = `Bearer ${token}`;
    }
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
  const baseResult = tryGetPublicStrategistApiBaseUrl();
  if (!baseResult.ok) {
    const demo = demoFallback<T>(path);
    if (demo) return { ...demo, rawText: JSON.stringify(demo.data) };
    throw baseResult.error;
  }
  const base = baseResult.baseUrl;
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
    const demo = demoFallback<T>(path);
    if (demo) return { ...demo, rawText: JSON.stringify(demo.data) };
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
