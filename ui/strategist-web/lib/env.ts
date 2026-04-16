export type StrategistWebEnv = {
  backendBaseUrl: string;
  backendTimeoutMs: number;
  forceMocks: boolean;
  strictBackend: boolean;
  usingMocks: boolean;
};

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
  const backendBaseUrl = normalizeBaseUrl(process.env.STRATEGIST_BACKEND_BASE_URL);
  const backendTimeoutMs = normalizeTimeout(process.env.STRATEGIST_BACKEND_TIMEOUT_MS);
  const forceMocks = normalizeBoolean(process.env.STRATEGIST_FORCE_MOCKS);
  const strictBackend = normalizeBoolean(process.env.STRATEGIST_STRICT_BACKEND);
  return {
    backendBaseUrl,
    backendTimeoutMs,
    forceMocks,
    strictBackend,
    usingMocks: forceMocks || (!strictBackend && !backendBaseUrl),
  };
}

export const getFrontendEnvConfig = getStrategistWebEnv;
