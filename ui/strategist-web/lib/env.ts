export type StrategistWebEnv = {
  backendBaseUrl: string;
  backendApiToken: string;
  backendTimeoutMs: number;
  forceMocks: boolean;
  strictBackend: boolean;
  usingMocks: boolean;
};

function isProductionRuntime(): boolean {
  return (process.env.NODE_ENV ?? "").trim().toLowerCase() === "production";
}

function normalizeBaseUrl(value: string | undefined): string {
  return (value ?? "").trim().replace(/\/$/, "");
}

function normalizeTimeout(value: string | undefined): number {
  const parsed = Number(value ?? "5000");
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 5000;
}

function normalizeBoolean(value: string | undefined): boolean {
  const normalized = (value ?? "").trim().toLowerCase();
  return normalized === "1" || normalized === "true" || normalized === "yes" || normalized === "on";
}

export function getStrategistWebEnv(): StrategistWebEnv {
  const isProd = isProductionRuntime();
  const backendBaseUrl = normalizeBaseUrl(process.env.STRATEGIST_BACKEND_BASE_URL);
  const backendApiToken = (process.env.STRATEGIST_BACKEND_API_TOKEN ?? "").trim();
  const backendTimeoutMs = normalizeTimeout(process.env.STRATEGIST_BACKEND_TIMEOUT_MS);
  const forceMocks = !isProd && normalizeBoolean(process.env.STRATEGIST_FORCE_MOCKS);
  const strictBackend = isProd ? true : normalizeBoolean(process.env.STRATEGIST_STRICT_BACKEND);
  return {
    backendBaseUrl,
    backendApiToken,
    backendTimeoutMs,
    forceMocks,
    strictBackend,
    usingMocks: forceMocks,
  };
}

export const getFrontendEnvConfig = getStrategistWebEnv;
