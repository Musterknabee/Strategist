import { fetchBurnIn, fetchRuntime, fetchWorkboard, getBackendRuntimeConfig } from "@/lib/server/backend";

export type FrontendPreflightCheck = {
  id: string;
  label: string;
  ok: boolean;
  detail: string;
  duration_ms: number;
};

export type FrontendPreflightReport = {
  generated_at: string;
  runtime: ReturnType<typeof getBackendRuntimeConfig>;
  checks: FrontendPreflightCheck[];
  guidance: string[];
};

async function runCheck<T>(
  id: string,
  label: string,
  fn: () => Promise<T>,
  detailBuilder: (payload: T) => { ok: boolean; detail: string },
): Promise<FrontendPreflightCheck> {
  const started = Date.now();
  try {
    const payload = await fn();
    const { ok, detail } = detailBuilder(payload);
    return { id, label, ok, detail, duration_ms: Date.now() - started };
  } catch (error) {
    return {
      id,
      label,
      ok: false,
      detail: error instanceof Error ? error.message : 'Unknown preflight failure',
      duration_ms: Date.now() - started,
    };
  }
}

export async function runFrontendPreflight(): Promise<FrontendPreflightReport> {
  const runtime = getBackendRuntimeConfig();
  const checks = await Promise.all([
    runCheck('runtime', 'Runtime payload', () => fetchRuntime(), (payload) => ({
      ok: Boolean(payload?.environment),
      detail: payload?.environment ? `environment=${payload.environment}` : 'Missing environment field',
    })),
    runCheck('workboard', 'Workboard payload', () => fetchWorkboard(), (payload) => ({
      ok: Array.isArray(payload?.queue?.entries),
      detail: Array.isArray(payload?.queue?.entries) ? `entries=${payload.queue.entries.length}` : 'Missing queue.entries array',
    })),
    runCheck('burnin', 'Burn-in payload', () => fetchBurnIn(), (payload) => ({
      ok: Array.isArray(payload?.metrics?.cpcvCoverage),
      detail: Array.isArray(payload?.metrics?.cpcvCoverage) ? `cpcv_points=${payload.metrics.cpcvCoverage.length}` : 'Missing metrics.cpcvCoverage array',
    })),
  ]);

  const guidance: string[] = [];
  if (!runtime.backendBaseUrl) {
    guidance.push('Set STRATEGIST_BACKEND_BASE_URL in .env.local to connect the web shell to the FastAPI UI routes.');
  }
  if (runtime.forceMocks) {
    guidance.push('STRATEGIST_FORCE_MOCKS is enabled, so all reads will intentionally stay on local mock payloads.');
  }
  if (!runtime.forceMocks && runtime.backendBaseUrl) {
    guidance.push('Backend base URL is configured; compare payload freshness in the shell against the Python /ui/* routes if results look unexpected.');
  }

  return {
    generated_at: new Date().toISOString(),
    runtime,
    checks,
    guidance,
  };
}

export const buildFrontendPreflightReport = runFrontendPreflight;
