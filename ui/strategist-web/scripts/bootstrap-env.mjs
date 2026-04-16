#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const cwd = process.cwd();
const examplePath = path.join(cwd, '.env.example');
const localPath = path.join(cwd, '.env.local');

if (!fs.existsSync(examplePath)) {
  console.error('[bootstrap-env] Missing .env.example');
  process.exit(1);
}

if (fs.existsSync(localPath)) {
  console.log('[bootstrap-env] .env.local already exists. No changes made.');
  process.exit(0);
}

fs.copyFileSync(examplePath, localPath);
console.log('[bootstrap-env] Created .env.local from .env.example');
console.log('[bootstrap-env] Next: review STRATEGIST_BACKEND_BASE_URL / STRATEGIST_FORCE_MOCKS, then run npm run doctor');
