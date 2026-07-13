#!/usr/bin/env node
/**
 * Archify render server — runs OUTSIDE the bwrap sandbox.
 * Accepts POST /render with a JSON body, returns a PNG.
 *
 * POST /render
 *   Body: { "type": "architecture", "data": { ...archify JSON IR... }, "scale": 3 }
 *   Response: image/png binary
 *
 * GET /health
 *   Response: 200 {"ok":true}
 *
 * Default port: 18800 (override with ARCHIFY_PORT env var).
 */

import http from 'node:http';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const archifyBin = path.join(__dirname, 'archify', 'bin', 'archify.mjs');
const watermarkScript = path.join(__dirname, 'watermark.py');
const PORT = Number(process.env.ARCHIFY_PORT) || 18800;

// ── Puppeteer discovery ────────────────────────────────────────────────────
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

const puppeteerPath = findPuppeteer();
if (!puppeteerPath) {
  console.error('[archify-server] Cannot find puppeteer bundled with @mermaid-js/mermaid-cli. Aborting.');
  process.exit(1);
}
const { default: puppeteer } = await import(puppeteerPath);
console.log(`[archify-server] puppeteer found: ${puppeteerPath}`);

// ── Core render function ───────────────────────────────────────────────────
async function renderToPng(type, diagramData, scale = 3) {
  const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const tmpJson = path.join(os.tmpdir(), `archify-${id}.json`);
  const tmpHtml = path.join(os.tmpdir(), `archify-${id}.html`);
  const tmpPng  = path.join(os.tmpdir(), `archify-${id}.png`);

  try {
    fs.writeFileSync(tmpJson, JSON.stringify(diagramData), 'utf8');

    const render = spawnSync(process.execPath, [archifyBin, 'render', type, tmpJson, tmpHtml], { encoding: 'utf8' });
    if (render.status !== 0) {
      throw new Error((render.stderr || render.stdout || '').trim() || `archify render exited ${render.status}`);
    }

    const check = spawnSync(process.execPath, [archifyBin, 'check', tmpHtml], { encoding: 'utf8' });
    let checkResult = null;
    try { checkResult = JSON.parse(check.stdout); } catch {}
    if (checkResult?.ok === false) {
      throw new Error('archify check failed: ' + JSON.stringify(checkResult));
    }

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
      await page.screenshot({ path: tmpPng, fullPage: true, omitBackground: false });
    } finally {
      await browser.close();
    }

    if (fs.existsSync(watermarkScript)) {
      spawnSync('python3', [watermarkScript, '--auto-project-name', tmpPng, '-o', tmpPng], { encoding: 'utf8' });
    }

    return fs.readFileSync(tmpPng);
  } finally {
    for (const f of [tmpJson, tmpHtml, tmpPng]) {
      try { fs.unlinkSync(f); } catch {}
    }
  }
}

// ── HTTP server ────────────────────────────────────────────────────────────
function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', c => chunks.push(c));
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    req.on('error', reject);
  });
}

const server = http.createServer(async (req, res) => {
  if (req.method === 'GET' && req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ ok: true }));
  }

  if (req.method === 'POST' && req.url === '/render') {
    let body;
    try {
      body = JSON.parse(await readBody(req));
    } catch {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ error: 'Invalid JSON body' }));
    }

    const { type, data, scale } = body;
    if (!type || !data) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ error: 'Missing required fields: type, data' }));
    }

    try {
      console.log(`[archify-server] render ${type} (scale=${scale || 3})`);
      const png = await renderToPng(type, data, scale || 3);
      res.writeHead(200, { 'Content-Type': 'image/png', 'Content-Length': png.length });
      res.end(png);
      console.log(`[archify-server] render OK (${png.length} bytes)`);
    } catch (err) {
      console.error(`[archify-server] render FAILED:`, err.message);
      res.writeHead(422, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
    return;
  }

  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Not found' }));
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`[archify-server] listening on http://127.0.0.1:${PORT}`);
});

process.on('SIGTERM', () => { server.close(); process.exit(0); });
process.on('SIGINT',  () => { server.close(); process.exit(0); });
