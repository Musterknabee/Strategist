import fs from "node:fs/promises";
import path from "node:path";

export type FrontendDiagnosticsHistoryEntry = {
  exportId: string;
  generatedAt: string;
  mode: "mock-backed" | "backend-connected";
  url?: string;
  status?: number;
  posture: string;
  runtimeEnvironment?: string;
  notesCount: number;
  probeCount: number;
  warningCount?: number;
};

export type FrontendDiagnosticsHistoryQuery = {
  limit?: number;
  mode?: FrontendDiagnosticsHistoryEntry["mode"] | "all";
  posture?: string | "all";
  search?: string;
};

const HISTORY_FILE = path.join(process.cwd(), "artifacts", "frontend-diagnostics.history.jsonl");

function normalizeLimit(limit?: number): number {
  if (!Number.isFinite(limit) || !limit || limit <= 0) {
    return 12;
  }
  return Math.floor(limit);
}

function normalizeSearch(value?: string): string {
  return (value ?? "").trim().toLowerCase();
}

function matchesQuery(entry: FrontendDiagnosticsHistoryEntry, query: FrontendDiagnosticsHistoryQuery): boolean {
  if (query.mode && query.mode !== "all" && entry.mode !== query.mode) {
    return false;
  }
  if (query.posture && query.posture !== "all" && entry.posture !== query.posture) {
    return false;
  }
  const search = normalizeSearch(query.search);
  if (!search) {
    return true;
  }
  const haystack = [
    entry.exportId,
    entry.generatedAt,
    entry.mode,
    entry.posture,
    entry.runtimeEnvironment,
    entry.url,
    String(entry.status ?? ""),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return haystack.includes(search);
}

export async function readFrontendDiagnosticsHistory(
  query: FrontendDiagnosticsHistoryQuery | number = 12
): Promise<FrontendDiagnosticsHistoryEntry[]> {
  const normalizedQuery: FrontendDiagnosticsHistoryQuery =
    typeof query === "number" ? { limit: query } : query;
  try {
    const raw = await fs.readFile(HISTORY_FILE, "utf8");
    const entries = raw
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => JSON.parse(line) as FrontendDiagnosticsHistoryEntry)
      .sort((a, b) => (a.generatedAt < b.generatedAt ? 1 : -1))
      .filter((entry) => matchesQuery(entry, normalizedQuery));
    return entries.slice(0, normalizeLimit(normalizedQuery.limit));
  } catch (error) {
    const code = (error as NodeJS.ErrnoException | undefined)?.code;
    if (code === "ENOENT") {
      return [];
    }
    throw error;
  }
}

export async function readLatestFrontendDiagnosticsHistoryEntry(): Promise<FrontendDiagnosticsHistoryEntry | null> {
  const [latest] = await readFrontendDiagnosticsHistory({ limit: 1 });
  return latest ?? null;
}
