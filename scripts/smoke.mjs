import { _electron as electron } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
mkdirSync('test-results', { recursive: true });
const empty = process.argv.includes('--empty');
const root = path.resolve('.');
const data = path.join(root, 'test-results', empty ? 'empty-profile' : 'smoke-profile');
mkdirSync(data, { recursive: true });
writeFileSync(path.join(data, 'settings.json'), JSON.stringify({ size: 280, yaw: 0, alwaysOnTop: true, position: { x: 600, y: 200 } }));
mkdirSync(path.join(root, 'test-results/empty-characters'), { recursive: true });
const env = { ...process.env, BA_TEST_DATA: data, ...(empty ? { BA_CHARACTERS: path.join(root, 'test-results/empty-characters') } : {}) };
delete env.ELECTRON_RUN_AS_NODE;
const app = await electron.launch({ ...(process.env.BA_EXECUTABLE ? { executablePath: path.resolve(process.env.BA_EXECUTABLE), args: [] } : { args: ['.'] }), env });
try {
  const page = await app.firstWindow();
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  await page.waitForFunction(() => window.petDiagnostics && (window.petDiagnostics.error || window.petDiagnostics.frames > 5));
  const result = await page.evaluate(() => window.petDiagnostics);
  await page.screenshot({ path: `test-results/${empty ? 'empty' : 'pet'}.png`, omitBackground: true });
  if (empty) {
    assert.match(result.error, /尚未安装/);
    assert.equal(await page.locator('#status').isVisible(), true);
  } else {
    assert.equal(result.error, null); assert.ok(result.bones > 0); assert.ok(result.meshes > 0);
    assert.equal(result.action, 'idle');
  }
  assert.deepEqual(errors, []);
  const windowState = await app.evaluate(({ BrowserWindow }) => { const win = BrowserWindow.getAllWindows()[0]; return { visible: win.isVisible(), top: win.isAlwaysOnTop(), resizable: win.isResizable(), bounds: win.getBounds() }; });
  console.log({ windowState });
  assert.equal(windowState.top, true); assert.equal(windowState.resizable, false);
  writeFileSync(`test-results/${empty ? 'empty' : 'smoke'}.json`, JSON.stringify({ result, windowState, errors }, null, 2));
  console.log(JSON.stringify({ result, windowState }));
} finally { await app.close(); }
