#!/usr/bin/env node
// Render an archify JSON IR file to PNG.
// Usage: node render_archify.mjs <type> <input.json> <output.png> [scale]
//
// Preferred path: POST to archify-server (http://127.0.0.1:18800/render),
// which runs outside the bwrap sandbox and has full Puppeteer/Chrome access.
// Fallback: run Puppeteer locally (only works outside the sandbox).

import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const archifyBin = path.join(__dirname, 'archify', 'bin', 'archify.mjs');
const watermarkScript = path.join(__dirname, 'watermark.py');

const [, , type, input, output, scaleArg] = process.argv;
if (!type || !input || !output) {
  console.error('Usage: node render_archify.mjs <type> <input.json> <output.png> [scale]');
  process.exit(2);
}
const scale = Number(scaleArg) || 3;
const ARCHIFY_SERVER = `http://127.0.0.1:${process.env.ARCHIFY_PORT || 18800}`;

// ── Try the render server first ────────────────────────────────────────────
function httpPost(url, body) {
  return new Promise((resolve, reject) => {
    const payload = Buffer.from(JSON.stringify(body), 'utf8');
    const u = new URL(url);
    const req = http.request({ hostname: u.hostname, port: u.port, path: u.pathname,
      method: 'POST', headers: { 'Content-Type': 'application/json', 'Content-Length': payload.length } },
      res => {
        const chunks = [];
        res.on('data', c => chunks.push(c));
        res.on('end', () => resolve({ status: res.statusCode, body: Buffer.concat(chunks) }));
      });
    req.on('error', reject);
    req.setTimeout(120_000, () => { req.destroy(new Error('timeout')); });
    req.write(payload);
    req.end();
  });
}

async function tryServer() {
  // Quick health check (1 s timeout).
  const alive = await new Promise(resolve => {
    const req = http.get(`${ARCHIFY_SERVER}/health`, res => {
      res.resume();
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(1000, () => { req.destroy(); resolve(false); });
  });
  if (!alive) return false;

  const data = JSON.parse(fs.readFileSync(input, 'utf8'));
  const result = await httpPost(`${ARCHIFY_SERVER}/render`, { type, data, scale });
  if (result.status !== 200) {
    const msg = result.body.toString('utf8');
    console.error(`[render_archify] server returned ${result.status}: ${msg}`);
    process.exit(1);
  }
  fs.writeFileSync(output, result.body);
  return true;
}

// ── Local Puppeteer fallback ───────────────────────────────────────────────
function run(args) {
  const result = spawnSync(process.execPath, args, { encoding: 'utf8' });
  if (result.status !== 0) {
    console.error(result.stdout || '');
    console.error(result.stderr || '');
    process.exit(result.status ?? 1);
  }
  return result.stdout;
}

function findPuppeteer() {
  const nodeExecDir = path.dirname(process.execPath);
  const nodeModulesGlobal = path.resolve(nodeExecDir, '..', 'lib', 'node_modules');
  const candidates = [
    path.join(nodeModulesGlobal, '@mermaid-js', 'mermaid-cli', 'node_modules', 'puppeteer', 'lib', 'esm', 'puppeteer', 'puppeteer.js'),
  ];
  const mmdc = spawnSync('which', ['mmdc'], { encoding: 'utf8' }).stdout.trim();
  if (mmdc) {
    const prefix = path.resolve(path.dirname(mmdc), '..');
    candidates.push(path.join(prefix, 'lib', 'node_modules', '@mermaid-js', 'mermaid-cli', 'node_modules', 'puppeteer', 'lib', 'esm', 'puppeteer', 'puppeteer.js'));
  }
  return candidates.find(c => fs.existsSync(c)) || null;
}

async function localRender() {
  const tmpHtml = path.join(os.tmpdir(), `archify-${Date.now()}-${Math.random().toString(36).slice(2)}.html`);
  run([archifyBin, 'render', type, input, tmpHtml]);

  const checkOut = run([archifyBin, 'check', tmpHtml]);
  let checkResult = null;
  try { checkResult = JSON.parse(checkOut); } catch {}
  if (checkResult?.ok === false) {
    console.error('archify check failed:', JSON.stringify(checkResult, null, 2));
    fs.unlinkSync(tmpHtml);
    process.exit(1);
  }

  const puppeteerPath = findPuppeteer();
  if (!puppeteerPath) {
    console.error('archify-server is not running and puppeteer not found locally.');
    console.error(`Start the server first: node scripts/archify-server.mjs`);
    fs.unlinkSync(tmpHtml);
    process.exit(1);
  }

  const { default: puppeteer } = await import(puppeteerPath);
  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1600, height: 900, deviceScaleFactor: scale });
    await page.goto(`file://${tmpHtml}?theme=light`, { waitUntil: 'load' });
    await page.waitForSelector('.diagram-container svg');
    await page.evaluate(() => {
      ['.toolbar', '.footer'].forEach(sel => {
        const el = document.querySelector(sel);
        if (el) el.style.display = 'none';
      });
    });
    await page.screenshot({ path: output, fullPage: true, omitBackground: false });
  } finally {
    await browser.close();
    fs.unlinkSync(tmpHtml);
  }
}

// ── Main ───────────────────────────────────────────────────────────────────
const usedServer = await tryServer();
if (!usedServer) {
  console.log('[render_archify] archify-server not running, using local Puppeteer');
  await localRender();
}

if (fs.existsSync(watermarkScript)) {
  const wm = spawnSync('python3', [watermarkScript, '--auto-project-name', output, '-o', output], { encoding: 'utf8' });
  if (wm.stdout?.includes('Watermarked')) {
    console.log(`Added watermark to ${output}`);
  }
}

console.log(`OK: ${output}`);
