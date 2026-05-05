/**
 * Browser-safe configuration only. Never read secrets here.
 */

export class StrategistConfigError extends Error {
  readonly name = "StrategistConfigError";
}

/** Normalize API origin/base: trim, strip trailing slashes, validate http(s). */
export function normalizeStrategistApiBaseUrl(raw: string): string {
  const trimmed = raw.trim().replace(/\/+$/, "");
  if (!trimmed) {
    throw new StrategistConfigError("Strategist API base URL is empty");
  }
  let url: URL;
  try {
    url = new URL(trimmed);
  } catch {
    throw new StrategistConfigError(`Strategist API base URL is not a valid URL: ${raw}`);
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new StrategistConfigError("Strategist API base URL must use http or https");
  }
  return trimmed;
}

/**
 * Public API base for browser fetches to `/ui/*`.
 * Production builds must set `NEXT_PUBLIC_STRATEGIST_API_BASE_URL`.
 * Development defaults to loopback API if unset.
 */
export function getPublicStrategistApiBaseUrl(): string {
  const fromEnv = process.env.NEXT_PUBLIC_STRATEGIST_API_BASE_URL?.trim();
  if (fromEnv) {
    return normalizeStrategistApiBaseUrl(fromEnv);
  }
  if (process.env.NODE_ENV === "development") {
    return normalizeStrategistApiBaseUrl("http://127.0.0.1:8000");
  }
  throw new StrategistConfigError(
    "NEXT_PUBLIC_STRATEGIST_API_BASE_URL is required for production builds (browser read-plane)",
  );
}

export function tryGetPublicStrategistApiBaseUrl():
  | { ok: true; baseUrl: string }
  | { ok: false; error: StrategistConfigError } {
  try {
    return { ok: true, baseUrl: getPublicStrategistApiBaseUrl() };
  } catch (e) {
    if (e instanceof StrategistConfigError) {
      return { ok: false, error: e };
    }
    throw e;
  }
}

export function isStrategistDemoModeEnabled(): boolean {
  return process.env.NEXT_PUBLIC_STRATEGIST_DEMO_MODE?.trim().toLowerCase() === "true";
}
