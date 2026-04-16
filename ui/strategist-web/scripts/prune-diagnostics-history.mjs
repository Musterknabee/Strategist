import fs from 'node:fs/promises';
import path from 'node:path';

const root = process.cwd();
const outDir = path.join(root, 'artifacts');
const historyFile = path.join(outDir, 'frontend-diagnostics.history.jsonl');
const keep = Number.parseInt(process.env.STRATEGIST_DIAGNOSTICS_HISTORY_KEEP || '50', 10);

try {
  const raw = await fs.readFile(historyFile, 'utf8');
  const entries = raw
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line))
    .sort((a, b) => (a.generatedAt < b.generatedAt ? 1 : -1));

  const kept = entries.slice(0, Number.isFinite(keep) && keep > 0 ? keep : 50);
  await fs.mkdir(outDir, { recursive: true });
  await fs.writeFile(historyFile, kept.map((entry) => JSON.stringify(entry)).join('\n') + (kept.length ? '\n' : ''));

  console.log(`Pruned diagnostics history to ${kept.length} entries at ${historyFile}`);
} catch (error) {
  const code = error && typeof error === 'object' ? error.code : undefined;
  if (code === 'ENOENT') {
    console.log(`No diagnostics history file found at ${historyFile}`);
    process.exit(0);
  }
  console.error('Failed to prune diagnostics history');
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
}
