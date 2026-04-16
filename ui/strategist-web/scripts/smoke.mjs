#!/usr/bin/env node
const baseUrl = (process.env.STRATEGIST_WEB_BASE_URL || 'http://localhost:3000').replace(/\/$/, '');
const endpoints = [
  { label: 'health', path: '/api/ui/health' },
  { label: 'runtime', path: '/api/ui/runtime' },
  { label: 'workboard', path: '/api/ui/workboard' },
  { label: 'burn-in', path: '/api/ui/burn-in' },
  { label: 'preflight', path: '/api/ui/preflight' },
];

async function probe(endpoint) {
  const started = Date.now();
  try {
    const response = await fetch(`${baseUrl}${endpoint.path}`, {
      headers: { accept: 'application/json' },
    });
    const durationMs = Date.now() - started;
    const text = await response.text();
    let body;
    try {
      body = JSON.parse(text);
    } catch {
      body = { raw: text.slice(0, 160) };
    }
    const ok = response.ok;
    return {
      ...endpoint,
      ok,
      status: response.status,
      durationMs,
      preview:
        typeof body === 'object' && body !== null
          ? JSON.stringify(body).slice(0, 180)
          : String(body).slice(0, 180),
    };
  } catch (error) {
    return {
      ...endpoint,
      ok: false,
      status: 'ERR',
      durationMs: Date.now() - started,
      preview: error instanceof Error ? error.message : String(error),
    };
  }
}

const results = await Promise.all(endpoints.map(probe));
console.log(`[smoke] Probing Strategist web shell at ${baseUrl}`);
for (const result of results) {
  console.log(`- ${result.label.padEnd(10)} status=${String(result.status).padEnd(3)} ok=${result.ok ? 'yes' : 'no '} duration=${String(result.durationMs).padStart(4)}ms`);
  console.log(`  ${result.preview}`);
}

if (results.some((item) => !item.ok)) {
  console.error('[smoke] One or more probes failed. Inspect the preview lines above.');
  process.exit(1);
}

console.log('[smoke] All probes succeeded.');
