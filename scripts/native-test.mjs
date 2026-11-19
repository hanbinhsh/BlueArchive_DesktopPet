import { _electron as electron } from 'playwright';
import { mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import path from 'node:path';
import assert from 'node:assert/strict';
const run = promisify(execFile);
const root = path.resolve('.');
const profile = path.join(root, 'test-results/native-profile');
mkdirSync(profile, { recursive: true });
writeFileSync(path.join(profile, 'settings.json'), JSON.stringify({ character: 'serika', size: 280, yaw: 0, alwaysOnTop: true, position: { x: 200, y: 180 } }));
const env = { ...process.env, BA_TEST_DATA: profile }; delete env.ELECTRON_RUN_AS_NODE;
let app = await electron.launch({ args: ['.'], env });
const checks = [];
async function input(actions) {
  const file = path.join(root, 'test-results/native-actions.json');
  writeFileSync(file, JSON.stringify(actions));
  const result = await run('powershell.exe', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', path.join(root, 'scripts/native-input.ps1'), '-ActionsFile', file], { windowsHide: true });
  console.log(result.stdout);
}
async function physical(x, y) { return app.evaluate(({ screen }, p) => screen.dipToScreenPoint(p), { x, y }); }
try {
  let page = await app.firstWindow(); await page.waitForFunction(() => window.petDiagnostics?.frames > 5);
  await page.evaluate(() => { window.nativeEvents = []; for (const name of ['mousemove', 'pointermove', 'pointerdown', 'pointerup', 'blur']) window.addEventListener(name, e => window.nativeEvents.push({ name, x: e.clientX, y: e.clientY, sx: e.screenX, sy: e.screenY, hit: window.petDiagnostics.hit })); });
  await app.evaluate(async ({ BrowserWindow }) => {
    const pet = BrowserWindow.getAllWindows()[0];
    globalThis.petTestId = pet.id;
    const underlay = new BrowserWindow({ ...pet.getBounds(), frame: false, backgroundColor: '#d6eef8', show: false, webPreferences: { contextIsolation: true, nodeIntegration: false } });
    globalThis.underlayTestId = underlay.id;
    await underlay.loadURL('data:text/html,<html><body style="margin:0;background:%23d6eef8;height:100vh"><script>window.clickCount=0;document.addEventListener("click",()=>window.clickCount++)</script></body></html>');
    underlay.show(); pet.showInactive();
  });
  await page.waitForTimeout(400);
  console.log(await app.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows().map(w => ({ id: w.id, hwnd: w.getNativeWindowHandle().readUInt32LE(), bounds: w.getBounds(), visible: w.isVisible() }))));
  const empty = await physical(210, 190);
  await input([{ type: 'move', ...empty }, { type: 'wait', ms: 350 }, { type: 'down' }, { type: 'wait', ms: 80 }, { type: 'up' }, { type: 'wait', ms: 200 }]);
  const clicks = await app.evaluate(async ({ BrowserWindow }) => BrowserWindow.fromId(globalThis.underlayTestId).webContents.executeJavaScript('window.clickCount'));
  console.log({ empty, clicks, diagnostics: await page.evaluate(() => window.petDiagnostics) });
  assert.equal(clicks, 1);
  checks.push('Native click passes through transparent area to underlying test window');
  // Full official prefab's animated head is right of its bind-pose centre.
  const face = await physical(460, 360);
  const moved = await physical(540, 410);
  const halfway = await physical(465, 365);
  await input([{ type: 'move', ...face }, { type: 'wait', ms: 400 }, { type: 'down' }, { type: 'wait', ms: 100 }, { type: 'move', ...halfway }, { type: 'wait', ms: 120 }, { type: 'move', ...moved }, { type: 'wait', ms: 250 }, { type: 'up' }, { type: 'wait', ms: 200 }]);
  const bounds = await app.evaluate(({ BrowserWindow }) => BrowserWindow.fromId(globalThis.petTestId).getBounds());
  writeFileSync('test-results/native-events.json', JSON.stringify(await page.evaluate(() => window.nativeEvents), null, 2));
  await page.screenshot({ path: 'test-results/native-pet.png', omitBackground: true });
  assert.ok(bounds.x > 250 && bounds.y > 210, JSON.stringify(bounds));
  assert.equal(await page.evaluate(() => window.petDiagnostics.action), 'idle');
  checks.push('Native drag moves the window and does not trigger click animation');
  await page.evaluate(() => { window.pet.resize(360); window.pet.rotate(.4); });
  await page.waitForTimeout(400);
  await app.close();
  const saved = JSON.parse(readFileSync(path.join(profile, 'settings.json'), 'utf8'));
  assert.equal(saved.size, 360); assert.equal(saved.yaw, .4);
  app = await electron.launch({ args: ['.'], env });
  page = await app.firstWindow(); await page.waitForFunction(() => window.petDiagnostics?.frames > 5);
  const restored = await page.evaluate(async () => (await window.pet.init()).settings);
  assert.equal(restored.size, 360); assert.equal(restored.yaw, .4); assert.deepEqual(restored.position, saved.position);
  checks.push('Restart restores position, size and rotation');
  writeFileSync('test-results/native.json', JSON.stringify({ checks, bounds, saved, restored }, null, 2));
  console.log(checks.join('\n'));
} finally { await app.close(); }
