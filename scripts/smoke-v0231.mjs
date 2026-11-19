import { openTestPanel } from './themed-menu-test-helper.mjs';
import { _electron as electron } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const checks = [
  { character: 'pina', furniture: 'f7106_0' },
  { character: 'reisa', furniture: 'f9106_0' },
  { character: 'renge_swimsuit', furniture: 'f210371_0' },
  { character: 'sena', furniture: null },
  { character: 'sena', furniture: 'f10_0' },
  { character: 'serina_christmas', furniture: null },
  { character: 'yukari_swimsuit', furniture: 'f13302_0' },
  { character: 'yuzu_maid', furniture: null, action: 'interact' },
  { character: 'cherino_onsen', furniture: 'f6203_0' },
  { character: 'fubuki_swimsuit', furniture: 'f210344_0' },
  { character: 'sakurako_idol', furniture: 'f210354_0' },
  { character: 'sakurako_idol', furniture: 'f210354_1' },
  { character: 'mari_idol', furniture: 'f210354_0' },
  { character: 'mine_idol', furniture: 'f210354_0' },
];

const exe = path.resolve('release/v0.2.31/win-unpacked/BA Desktop Pet.exe');
const profile = path.resolve('test-results/smoke-v0231-profile');
mkdirSync(profile, { recursive: true });
writeFileSync(
  path.join(profile, 'settings.json'),
  JSON.stringify({ character: 'pina', size: 360, position: { x: 450, y: 180 }, eyeFollow: false, allowOffscreen: true }),
);

const env = { ...process.env, BA_TEST_DATA: profile };
delete env.ELECTRON_RUN_AS_NODE;

const app = await electron.launch({ executablePath: exe, args: [], env });
const errors = [];
const checked = [];

try {
  const page = await app.firstWindow();
  await app.context().setOffline(true);
  page.on('pageerror', (e) => { errors.push('PAGEERROR: ' + String(e)); console.error('PAGEERROR', e); });
  page.on('console', (e) => { if (e.type() === 'error') { errors.push('CONSOLE: ' + e.text()); console.error('CONSOLE', e.text()); } });

  const panel = await openTestPanel(app, page);
  await app.evaluate(({ BrowserWindow }) => {
    const w = BrowserWindow.getAllWindows().find((w) => w.webContents.getURL().endsWith('/index.html'));
    w.setFocusable(false);
    w.setBounds({ ...w.getBounds(), x: -4000, y: 180 });
  });

  // Check search box aliases in packaged exe!
  for (const [q, expectedId] of [['玛丽娜', 'marina'], ['玲女', 'reijo'], ['高音', 'takane'], ['真里奈', 'marina'], ['丽情', 'reijo'], ['贵音', 'takane']]) {
    await panel.fill('#search', q);
    await panel.waitForTimeout(80);
    const count = await panel.locator(`[data-character="${expectedId}"]`).count();
    assert.ok(count >= 1, `Packaged search "${q}" must find ${expectedId}`);
    checked.push({ type: 'search', query: q, expectedId });
  }
  await panel.fill('#search', '');

  let current = 'pina';
  for (const item of checks) {
    if (current !== item.character) {
      const loaded = page.waitForEvent('load');
      await panel.evaluate((x) => window.panel.command('select', x), item.character);
      await loaded;
      current = item.character;
    }
    await page.waitForFunction(() => window.petDiagnostics?.frames > 5 && !window.petDiagnostics.loading, { timeout: 20000 });
    assert.equal(await page.evaluate(() => window.petDiagnostics.error), null, item.character);

    if (item.furniture) {
      await panel.evaluate((fid) => window.panel.command('furniture', fid), item.furniture);
      await page.waitForFunction((fid) => window.petDiagnostics?.sceneAction === fid && !window.petDiagnostics.loading && window.petDiagnostics.frames > 3, item.furniture, { timeout: 25000 });
      assert.equal(await page.evaluate(() => window.petDiagnostics.error), null, `${item.character}/${item.furniture}`);
      if (item.character === 'sena' && item.furniture === 'f10_0') {
        const mt = await page.evaluate(() => window.petDiagnostics.mouthTile);
        assert.equal(mt, 401, 'Sena table must start with closed mouth tile 401');
      }
      checked.push({ type: 'furniture', character: item.character, id: item.furniture });
      await panel.evaluate(() => window.panel.command('furniture', ''));
      await page.waitForFunction(() => window.petDiagnostics?.sceneKey === 'model.glb' && !window.petDiagnostics.loading, { timeout: 20000 });
    } else if (item.action) {
      await panel.evaluate((aid) => window.panel.command('action', aid), item.action);
      await page.waitForTimeout(200);
      assert.equal(await page.evaluate(() => window.petDiagnostics.error), null, `${item.character}:${item.action}`);
      checked.push({ type: 'action', character: item.character, id: item.action });
    } else {
      if (item.character === 'sena') {
        const mt = await page.evaluate(() => window.petDiagnostics.mouthTile);
        assert.equal(mt, 401, 'Sena idle must use closed mouth tile 401');
      }
      checked.push({ type: 'character', character: item.character });
    }
    console.log('OK:', item.character, item.furniture || item.action || 'idle');
  }

  assert.deepEqual(errors, []);
  writeFileSync('test-results/smoke-v0231.json', JSON.stringify({ exe, checked, errors }, null, 2));
  console.log(`SMOKE TEST PASSED: ${checked.length} checks, 0 errors`);
} finally {
  await app.close();
}
