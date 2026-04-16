import fs from 'node:fs/promises';
import path from 'node:path';

const root = process.cwd();
const outDir = path.join(root, 'artifacts');
const outFile = path.join(outDir, 'frontend-diagnostics.snapshot.json');
const historyFile = path.join(outDir, 'frontend-diagnostics.history.jsonl');
const baseUrl = process.env.STRATEGIST_WEB_BASE_URL || 'http://localhost:3000';
const url = `${baseUrl.replace(/\/$/, '')}/api/ui/diagnostics/export`;

const started = Date.now();

try {
  const response = await fetch(url);
  const text = await response.text();
  let payload;
  try {
    payload = JSON.parse(text);
  } catch {
    payload = { raw: text };
  }

  const snapshot = {
    fetchedAt: new Date().toISOString(),
    url,
    status: response.status,
    durationMs: Date.now() - started,
    payload,
  };

  await fs.mkdir(outDir, { recursive: true });
  await fs.writeFile(outFile, JSON.stringify(snapshot, null, 2));

  if (payload && typeof payload === 'object' && payload.exportId && payload.generatedAt) {
    const historyEntry = {
      exportId: payload.exportId,
      generatedAt: payload.generatedAt,
      mode: payload.mode,
      posture: payload.preflight?.posture ?? 'unknown',
      runtimeEnvironment: payload.runtime?.environment,
      notesCount: Array.isArray(payload.notes) ? payload.notes.length : 0,
      probeCount: Array.isArray(payload.preflight?.probes) ? payload.preflight.probes.length : 0,
      warningCount: typeof payload.metadata?.warningCount === 'number' ? payload.metadata.warningCount : 0,
      url,
      status: response.status,
    };
    await fs.appendFile(historyFile, `${JSON.stringify(historyEntry)}\n`);
  }

  console.log(`Diagnostics export written to ${outFile}`);
  console.log(`HTTP ${response.status} in ${Date.now() - started}ms`);
} catch (error) {
  console.error(`Failed to export diagnostics from ${url}`);
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
}
