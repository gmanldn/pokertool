#!/usr/bin/env node
'use strict';

const { spawnSync } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const projectRoot = path.resolve(__dirname, '..');
const lockPath = path.join(projectRoot, 'package-lock.json');
const nodeModulesPath = path.join(projectRoot, 'node_modules');
const stampPath = path.join(nodeModulesPath, '.deps-lock');

const hashFile = (filePath) => {
  try {
    const data = fs.readFileSync(filePath);
    return crypto.createHash('sha256').update(data).digest('hex');
  } catch (error) {
    return null;
  }
};

const expectedHash = hashFile(lockPath);
if (!expectedHash) {
  console.warn('[ensure-deps] package-lock.json not found; skipping dependency check');
  process.exit(0);
}

let currentHash = null;
try {
  currentHash = fs.readFileSync(stampPath, 'utf8').trim();
} catch (error) {
  currentHash = null;
}

const dependenciesMissing = !fs.existsSync(nodeModulesPath) || currentHash !== expectedHash;

if (!dependenciesMissing) {
  console.log('[ensure-deps] Frontend dependencies already up to date');
  process.exit(0);
}

console.log('[ensure-deps] Installing frontend dependencies...');
const result = spawnSync('npm', ['install', '--no-fund', '--no-audit'], {
  stdio: 'inherit',
  cwd: projectRoot,
  env: process.env,
});

if (result.status !== 0) {
  console.error('[ensure-deps] npm install failed');
  process.exit(result.status ?? 1);
}

fs.mkdirSync(nodeModulesPath, { recursive: true });
fs.writeFileSync(stampPath, expectedHash);
console.log('[ensure-deps] Frontend dependencies installed successfully');
