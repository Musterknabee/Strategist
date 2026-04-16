import { mockBurnIn, mockCommandReceipt, mockEvidence, mockPackDetail, mockRuntime, mockTribunal, mockWorkboard } from "@/lib/mocks/ui";
import type { UiOperatorCommandReceipt } from "@/lib/contracts/ui";
import { getStrategistWebEnv } from "@/lib/env";

const { backendBaseUrl, backendTimeoutMs, forceMocks, strictBackend, usingMocks } = getStrategistWebEnv();

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
    const response = await fetch(
      `${backendBaseUrl}${path}`,
      withTimeout({
        cache: "no-store",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
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

export function getBackendRuntimeConfig() {
  return {
    backendBaseUrl,
    backendTimeoutMs: Number.isFinite(backendTimeoutMs) ? backendTimeoutMs : 5000,
    forceMocks,
    strictBackend,
    usingMocks,
  };
}

export function fetchWorkboard() {
  return fetchJson("/ui/workboard", mockWorkboard);
}

export function fetchBurnIn() {
  return fetchJson("/ui/burnin", mockBurnIn);
}

export function fetchPackDetail(query: { pack_kind?: string; manifest_path?: string } = {}) {
  const params = new URLSearchParams();
  if (query.pack_kind) params.set("pack_kind", query.pack_kind);
  if (query.manifest_path) params.set("manifest_path", query.manifest_path);
  const suffix = params.size ? `?${params.toString()}` : "";
  return fetchJson(`/ui/packs/detail${suffix}`, mockPackDetail);
}

export function submitUiCommand(action: string, payload: Record<string, unknown>) {
  const fallback: UiOperatorCommandReceipt = { ...mockCommandReceipt, action };
  return fetchJson(`/ui/commands/${action}`, fallback, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchTribunal() {
  return fetchJson("/ui/tribunal", mockTribunal);
}

export function fetchEvidence() {
  return fetchJson("/ui/evidence", mockEvidence);
}

export function fetchRuntime(role?: string) {
  const suffix = role ? `?role=${encodeURIComponent(role)}` : "";
  return fetchJson(`/ui/runtime${suffix}`, mockRuntime);
}
