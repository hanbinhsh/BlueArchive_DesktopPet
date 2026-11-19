import { _electron as electron } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const env = { ...process.env, BA_TEST_DATA: path.resolve('test-results/actions-profile') };
delete env.ELECTRON_RUN_AS_NODE;
mkdirSync(env.BA_TEST_DATA, { recursive: true });
writeFileSync(path.join(env.BA_TEST_DATA, 'settings.json'), JSON.stringify({ character: 'serika', size: 360, yaw: 0, alwaysOnTop: true, position: { x: 500, y: 200 } }));
const app = await electron.launch({ ...(process.env.BA_EXECUTABLE ? { executablePath: path.resolve(process.env.BA_EXECUTABLE), args: [] } : { args: ['.'] }), env });
try {
  const page = await app.firstWindow();
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  await page.waitForFunction(() => window.petDiagnostics?.frames > 5);
  // Capture the real native menu constructed for a renderer request, then
  // invoke its real item callbacks without taking over the system mouse.
  await app.evaluate(({ Menu }) => { Menu.prototype.popup = function () { globalThis.actionTestMenu = this; }; });
  await page.evaluate(() => window.pet.menu());
  const labels = await app.evaluate(() => globalThis.actionTestMenu.items.find(i => i.label === '动作').submenu.items.map(i => i.label));
  assert.deepEqual(labels, ['待机', '咖啡厅互动', '原地走路', '胜利动作', '换弹', '编队提起']);
  async function select(id) {
    await app.evaluate(({ BrowserWindow }, id) => {
      const item = globalThis.actionTestMenu.getMenuItemById(`action-${id}`);
      item.click(item, BrowserWindow.getAllWindows()[0], {});
    }, id);
  }
  await page.evaluate(() => {
    window.mouthSamples = [];
    const sample = () => {
      const d = window.petDiagnostics;
      const last = window.mouthSamples.at(-1);
      if (!last || last.tile !== d.mouthTile || last.action !== d.action) window.mouthSamples.push({ action: d.action, time: d.actionTime, tile: d.mouthTile });
      requestAnimationFrame(sample);
    }; sample();
  });
  const results = [];
  for (const id of ['interact', 'walk', 'victory', 'reload', 'pickup']) {
    await select(id);
    await page.waitForFunction(id => window.petDiagnostics.action === id, id);
    await page.waitForTimeout(id === 'interact' ? 950 : 500);
    await page.screenshot({ path: `test-results/action-${id}.png`, omitBackground: true });
    await page.waitForFunction(() => window.petDiagnostics.action === 'idle', null, { timeout: 25000 });
    assert.equal(await page.evaluate(() => window.petDiagnostics.mouthTile), 402);
    results.push(`${id}: menu plays clip and returns to idle/default mouth`);
  }
  const samples = await page.evaluate(() => window.mouthSamples);
  assert.deepEqual(samples.filter(s => s.action === 'interact').map(s => s.tile), [402, 701, 703, 602, 402]);
  assert.deepEqual(samples.filter(s => s.action === 'victory').map(s => s.tile), [401, 402, 406]);
  await select('interact'); await page.waitForTimeout(220);
  await select('victory'); await page.waitForTimeout(100);
  await select('idle'); await page.waitForTimeout(250);
  assert.equal(await page.evaluate(() => window.petDiagnostics.action), 'idle');
  assert.equal(await page.evaluate(() => window.petDiagnostics.mouthTile), 402);
  assert.deepEqual(errors, []);
  writeFileSync('test-results/actions.json', JSON.stringify({ labels, results, samples, errors }, null, 2));
  console.log(results.join('\n'));
} finally { await app.close(); }
