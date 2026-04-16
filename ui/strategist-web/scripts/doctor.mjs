import fs from "node:fs";
import path from "node:path";

const cwd = process.cwd();
const envPath = path.join(cwd, ".env.local");
const examplePath = path.join(cwd, ".env.example");

function readEnvFile(filePath) {
  if (!fs.existsSync(filePath)) return {};
  const lines = fs.readFileSync(filePath, "utf8").split(/\r?\n/);
  const values = {};
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eqIndex = trimmed.indexOf("=");
    if (eqIndex === -1) continue;
    const key = trimmed.slice(0, eqIndex).trim();
    const value = trimmed.slice(eqIndex + 1).trim();
    values[key] = value;
  }
  return values;
}

function normalizeBoolean(value) {
  const normalized = String(value ?? "").trim().toLowerCase();
  return ["1", "true", "yes", "on"].includes(normalized);
}

function normalizeTimeout(value) {
  const parsed = Number(value ?? "5000");
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 5000;
}

function normalizeBaseUrl(value) {
  return String(value ?? "").trim().replace(/\/$/, "");
}

const source = fs.existsSync(envPath) ? envPath : examplePath;
const fileValues = readEnvFile(source);
const env = {
  STRATEGIST_BACKEND_BASE_URL:
    process.env.STRATEGIST_BACKEND_BASE_URL ?? fileValues.STRATEGIST_BACKEND_BASE_URL ?? "",
  STRATEGIST_BACKEND_TIMEOUT_MS:
    process.env.STRATEGIST_BACKEND_TIMEOUT_MS ?? fileValues.STRATEGIST_BACKEND_TIMEOUT_MS ?? "5000",
  STRATEGIST_FORCE_MOCKS:
    process.env.STRATEGIST_FORCE_MOCKS ?? fileValues.STRATEGIST_FORCE_MOCKS ?? "false",
};

const backendBaseUrl = normalizeBaseUrl(env.STRATEGIST_BACKEND_BASE_URL);
const backendTimeoutMs = normalizeTimeout(env.STRATEGIST_BACKEND_TIMEOUT_MS);
const forceMocks = normalizeBoolean(env.STRATEGIST_FORCE_MOCKS);
const usingMocks = forceMocks || !backendBaseUrl;

const lines = [
  "Strategist Web Doctor",
  `env source: ${fs.existsSync(envPath) ? ".env.local" : ".env.example"}`,
  `backend base URL: ${backendBaseUrl || "(not set)"}`,
  `backend timeout: ${backendTimeoutMs} ms`,
  `force mocks: ${forceMocks ? "enabled" : "disabled"}`,
  `effective mode: ${usingMocks ? "mock-backed" : "backend-connected"}`,
  "",
  "Recommended next steps:",
];

if (!fs.existsSync(envPath)) {
  lines.push("- Create .env.local first: cp .env.example .env.local");
}
if (!backendBaseUrl && !forceMocks) {
  lines.push("- Set STRATEGIST_BACKEND_BASE_URL for a live backend, or set STRATEGIST_FORCE_MOCKS=true for frontend-only work.");
}
if (usingMocks) {
  lines.push("- You are in mock-backed mode; use /settings/runtime and /settings/preflight to confirm the UI shell posture.");
} else {
  lines.push("- You are in backend-connected mode; ensure the Python service exposing /ui/* is running before npm run dev.");
}
lines.push("- Run npm run check");
lines.push("- Run npm run build");

console.log(lines.join("\n"));
