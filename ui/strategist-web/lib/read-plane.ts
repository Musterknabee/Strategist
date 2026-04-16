export type FreshnessTone = "fresh" | "aging" | "stale";

export type SurfaceProvenance = {
  generatedAtUtc?: string | null;
  sourceLabel: string;
  verificationLabel: string;
  verificationTone?: "verified" | "restricted" | "warning" | "neutral";
  projectionFamily?: string | null;
  trustLabel?: string | null;
  freezeActions?: boolean;
};

export function parseUtc(value?: string | null): number | null {
  if (!value) return null;
  const parsed = Date.parse(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function getFreshnessTone(
  generatedAtUtc?: string | null,
  thresholdsMs: { aging: number; stale: number } = { aging: 2 * 60_000, stale: 10 * 60_000 },
): FreshnessTone {
  const parsed = parseUtc(generatedAtUtc);
  if (parsed === null) return "stale";
  const age = Date.now() - parsed;
  if (age >= thresholdsMs.stale) return "stale";
  if (age >= thresholdsMs.aging) return "aging";
  return "fresh";
}

export function formatAge(generatedAtUtc?: string | null): string {
  const parsed = parseUtc(generatedAtUtc);
  if (parsed === null) return "timestamp unavailable";
  const ageMs = Math.max(0, Date.now() - parsed);
  const seconds = Math.floor(ageMs / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}

export function isReadPlaneDrifted(generatedAtUtc?: string | null, staleAfterMs = 10 * 60_000): boolean {
  const parsed = parseUtc(generatedAtUtc);
  if (parsed === null) return true;
  return Date.now() - parsed >= staleAfterMs;
}
