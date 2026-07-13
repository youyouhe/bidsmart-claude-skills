#!/usr/bin/env node
// Render an archify JSON IR file to PNG.
// Usage: node render_archify.mjs <type> <input.json> <output.png> [scale]
//
// type: architecture | workflow | sequence | dataflow | lifecycle
// scale: deviceScaleFactor for the screenshot (default 3)

import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const archifyBin = path.join(__dirname, 'archify', 'bin', 'archify.mjs');

const [, , type, input, output, scaleArg] = process.argv;
if (!type || !input || !output) {
  console.error('Usage: node render_archify.mjs <type> <input.json> <output.png> [scale]');
  process.exit(2);
}
const scale = Number(scaleArg) || 3;

const tmpHtml = path.join(os.tmpdir(), `archify-${Date.now()}-${Math.random().toString(36).slice(2)}.html`);

function run(args) {
  const result = spawnSync(process.execPath, args, { encoding: 'utf8' });
  if (result.status !== 0) {
    console.error(result.stdout || '');
    console.error(result.stderr || '');
    process.exit(result.status ?? 1);
  }
  return result.stdout;
}

run([archifyBin, 'render', type, input, tmpHtml]);

const checkOut = run([archifyBin, 'check', tmpHtml]);
let checkResult;
try {
  checkResult = JSON.parse(checkOut);
} catch {
  checkResult = null;
}
if (checkResult && checkResult.ok === false) {
  console.error('archify check failed:', JSON.stringify(checkResult, null, 2));
  fs.unlinkSync(tmpHtml);
  process.exit(1);
}

function findPuppeteer() {
  const globalRoot = spawnSync('npm', ['root', '-g'], { encoding: 'utf8' }).stdout.trim();
  const candidates = [
    path.join(globalRoot, '@mermaid-js', 'mermaid-cli', 'node_modules', 'puppeteer', 'lib', 'esm', 'puppeteer', 'puppeteer.js'),
  ];
  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  return null;
}

const puppeteerPath = findPuppeteer();
if (!puppeteerPath) {
  console.error('Could not locate puppeteer bundled with @mermaid-js/mermaid-cli. Rendered HTML left at: ' + tmpHtml);
  process.exit(1);
}

const { default: puppeteer } = await import(puppeteerPath);
const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
try {
  const page = await browser.newPage();
  // Wide enough for any diagram; height is auto-expanded via fullPage screenshot.
  await page.setViewport({ width: 1600, height: 900, deviceScaleFactor: scale });
  await page.goto(`file://${tmpHtml}?theme=light`, { waitUntil: 'load' });
  await page.waitForSelector('.diagram-container svg');
  // Hide interactive chrome that doesn't belong in a bid document PNG.
  await page.evaluate(() => {
    ['.toolbar', '.footer'].forEach(sel => {
      const el = document.querySelector(sel);
      if (el) el.style.display = 'none';
    });
  });
  // Full-page screenshot captures the diagram AND the cards below it.
  await page.screenshot({ path: output, fullPage: true, omitBackground: false });
} finally {
  await browser.close();
  fs.unlinkSync(tmpHtml);
}

const watermarkScript = path.join(__dirname, 'watermark.py');
if (fs.existsSync(watermarkScript)) {
  const wm = spawnSync('python3', [watermarkScript, '--auto-project-name', output, '-o', output], { encoding: 'utf8' });
  if (wm.stdout && wm.stdout.includes('Watermarked')) {
    console.log(`Added watermark to ${output}`);
  } else {
    console.log('Warning: Failed to add watermark (project name not found or error occurred)');
  }
}

console.log(`OK: ${output}`);
