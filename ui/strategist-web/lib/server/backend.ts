import { mockBurnIn, mockEvidence, mockPackDetail, mockRuntime, mockTribunal, mockWorkboard } from "@/lib/mocks/ui";
import type { UiOperatorCommandReceipt } from "@/lib/contracts/ui";
import { getStrategistWebEnv } from "@/lib/env";

const { backendApiToken, backendBaseUrl, backendTimeoutMs, forceMocks, strictBackend, usingMocks } = getStrategistWebEnv();

function withTimeout(init?: RequestInit): RequestInit {
  if (typeof AbortSignal !== "undefined" && typeof AbortSignal.timeout === "function") {
    return {
      ...init,
      signal: init?.signal ?? AbortSignal.timeout(Number.isFinite(backendTimeoutMs) ? backendTimeoutMs : 5000),
    };
  }
  return init ?? {};
}

async function parseJsonOrFallback<T>(response: Response, fallback: T): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

async function fetchJson<T>(path: string, fallback: T, init?: RequestInit): Promise<T> {
  if (!backendBaseUrl) {
    if (strictBackend && !forceMocks) {
      throw new Error(`Strict backend mode is enabled and STRATEGIST_BACKEND_BASE_URL is not configured for ${path}`);
    }
    return fallback;
  }

  try {
    const headers = new Headers(init?.headers);
    headers.set("Accept", "application/json");
    headers.set("Content-Type", "application/json");
    const method = (init?.method ?? "GET").toUpperCase();
    if (backendApiToken && method !== "GET" && method !== "HEAD") {
      headers.set("X-Strategy-Validator-Token", backendApiToken);
    }
    const response = await fetch(
      `${backendBaseUrl}${path}`,
      withTimeout({
        cache: "no-store",
        headers,
        ...init,
      }),
    );
    if (!response.ok) {
      if (strictBackend && !forceMocks) {
        throw new Error(`Backend request failed for ${path} with status ${response.status}`);
      }
      return fallback;
    }
    return parseJsonOrFallback(response, fallback);
  } catch (error) {
    if (strictBackend && !forceMocks) {
      throw error;
    }
    return fallback;
  }
}

async function fetchMutationJson<T>(path: string, init?: RequestInit): Promise<T> {
  if (!backendBaseUrl) {
    throw new Error(`Backend mutation route is unavailable for ${path}; configure STRATEGIST_BACKEND_BASE_URL before issuing governed mutations.`);
  }

  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  headers.set("Content-Type", "application/json");
  const method = (init?.method ?? "POST").toUpperCase();
  if (backendApiToken && method !== "GET" && method !== "HEAD") {
    headers.set("X-Strategy-Validator-Token", backendApiToken);
  }

  const response = await fetch(
    `${backendBaseUrl}${path}`,
    withTimeout({
      cache: "no-store",
      headers,
      ...init,
    }),
  );
  if (!response.ok) {
    throw new Error(`Backend mutation request failed for ${path} with status ${response.status}`);
  }
  return (await response.json()) as T;
}

async function fetchRequiredReadJson<T>(path: string, fallback: T, init?: RequestInit): Promise<T> {
  if (forceMocks) {
    return fallback;
  }

  if (!backendBaseUrl) {
    throw new Error(`Backend read route is unavailable for ${path}; configure STRATEGIST_BACKEND_BASE_URL before serving operator projections.`);
  }

  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  headers.set("Content-Type", "application/json");

  const response = await fetch(
    `${backendBaseUrl}${path}`,
    withTimeout({
      cache: "no-store",
      headers,
      ...init,
    }),
  );
  if (!response.ok) {
    throw new Error(`Backend read request failed for ${path} with status ${response.status}`);
  }
  return (await response.json()) as T;
}

export function getBackendRuntimeConfig() {
  return {
    backendApiTokenConfigured: backendApiToken.length > 0,
    backendBaseUrl,
    backendTimeoutMs: Number.isFinite(backendTimeoutMs) ? backendTimeoutMs : 5000,
    forceMocks,
    strictBackend,
    usingMocks,
  };
}

export function fetchWorkboard() {
  return fetchRequiredReadJson("/ui/workboard", mockWorkboard);
}

export function fetchBurnIn() {
  return fetchRequiredReadJson("/ui/burnin", mockBurnIn);
}

export function fetchPackDetail(query: { pack_kind?: string; manifest_path?: string } = {}) {
  const params = new URLSearchParams();
  if (query.pack_kind) params.set("pack_kind", query.pack_kind);
  if (query.manifest_path) params.set("manifest_path", query.manifest_path);
  const suffix = params.size ? `?${params.toString()}` : "";
  return fetchRequiredReadJson(`/ui/packs/detail${suffix}`, mockPackDetail);
}

export function submitUiCommand(action: string, payload: Record<string, unknown>) {
  return fetchMutationJson<UiOperatorCommandReceipt>(`/ui/commands/${action}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchTribunal() {
  return fetchRequiredReadJson("/ui/tribunal", mockTribunal);
}

export function fetchEvidence() {
  return fetchRequiredReadJson("/ui/evidence", mockEvidence);
}

export function fetchRuntime(role?: string) {
  const suffix = role ? `?role=${encodeURIComponent(role)}` : "";
  return fetchJson(`/ui/runtime${suffix}`, mockRuntime);
}
