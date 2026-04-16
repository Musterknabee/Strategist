import fs from 'node:fs/promises';
import path from 'node:path';

const historyFile = path.join(process.cwd(), 'artifacts', 'frontend-diagnostics.history.jsonl');

try {
  const raw = await fs.readFile(historyFile, 'utf8');
  const rows = raw
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line));

  const latest = rows.at(-1) ?? null;
  const summary = {
    totalRuns: rows.length,
    backendConnectedRuns: rows.filter((row) => row.mode === 'backend-connected').length,
    mockBackedRuns: rows.filter((row) => row.mode === 'mock-backed').length,
    warningRuns: rows.filter((row) => row.posture === 'warning').length,
    attentionRuns: rows.filter((row) => row.posture === 'attention').length,
    okRuns: rows.filter((row) => row.posture === 'ok').length,
    latestExportId: latest?.exportId ?? null,
    latestPosture: latest?.posture ?? null,
    latestMode: latest?.mode ?? null,
    latestGeneratedAt: latest?.generatedAt ?? null,
  };

  console.log(JSON.stringify(summary, null, 2));
} catch (error) {
  if ((error && typeof error === 'object' && 'code' in error && error.code === 'ENOENT')) {
    console.log(JSON.stringify({ totalRuns: 0, message: 'No diagnostics history file found yet.' }, null, 2));
    process.exit(0);
  }
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
}
