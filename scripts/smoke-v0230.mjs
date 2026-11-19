import { openTestPanel } from './themed-menu-test-helper.mjs';
import { _electron as electron } from 'playwright';
import { mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const specs = JSON.parse(readFileSync('scripts/roster-wave21.json', 'utf8'));
const ids = Object.keys(specs);
const fixedChecks = [
  { character: 'misaki', furniture: 'f1108_0' },
  { character: 'misaki', furniture: 'f1108_1' },
  { character: 'saori', furniture: 'f1108_0' },
  { character: 'saori', furniture: 'f1108_1' },
  { character: 'kokoro', furniture: 'f211314_0' },
  { character: 'kokoro', furniture: 'f211314_1' },
  { character: 'kotone', furniture: 'f211314_0' },
  { character: 'kotone', furniture: 'f211314_1' },
  { character: 'kirino', furniture: 'f211304_0' },
  { character: 'ako_dress', furniture: 'f15306_0' },
  { character: 'ako_dress', furniture: 'f15306_1' },
  { character: 'hina_dress', furniture: 'f15306_1' },
  { character: 'saori_dress', furniture: 'f210366_0', shot: 'test-results/v0230-final-saori-mirror.png', freeze: 4.0 },
  { character: 'shizuko', furniture: 'f203302_0' },
  { character: 'shizuko_swimsuit', furniture: 'f9302_0' },
  { character: 'nodoka_onsen', furniture: 'f6201_0' },
  { character: 'tsukuyo', furniture: 'f4106_0', shot: 'test-results/v0230-final-tsukuyo-pot.png', freeze: 3.5 },
  { character: 'tsukuyo_dress', furniture: 'f210389_0' },
];
const exe = path.resolve('release/v0.2.30/win-unpacked/BA Desktop Pet.exe');
const profile = path.resolve('test-results/smoke-v0230-profile');
mkdirSync(profile, { recursive: true });
writeFileSync(
  path.join(profile, 'settings.json'),
  JSON.stringify({ character: ids[0], size: 360, position: { x: 450, y: 180 }, eyeFollow: false, allowOffscreen: true }),
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

  let current = ids[0];
  const selectChar = async (id) => {
    if (current !== id) {
      const loaded = page.waitForEvent('load');
      await panel.evaluate((x) => window.panel.command('select', x), id);
      await loaded;
      current = id;
    }
    await page.waitForFunction(() => window.petDiagnostics?.frames > 5 && !window.petDiagnostics.loading, { timeout: 20000 });
    assert.equal(await page.evaluate(() => window.petDiagnostics.error), null, id);
  };

  for (const id of ids) {
    await selectChar(id);
    const diag = await page.evaluate(() => window.petDiagnostics);
    checked.push({ type: 'character', id, animations: diag.animations?.length || 0 });
    const manifest = JSON.parse(readFileSync(`characters/${id}/character.json`, 'utf8'));
    for (const f of manifest.furniture || []) {
      await panel.evaluate((fid) => window.panel.command('furniture', fid), f.id);
      await page.waitForFunction((fid) => window.petDiagnostics?.sceneAction === fid && !window.petDiagnostics.loading && window.petDiagnostics.frames > 3, f.id, { timeout: 25000 });
      assert.equal(await page.evaluate(() => window.petDiagnostics.error), null, `${id}/${f.id}`);
      checked.push({ type: 'furniture', character: id, id: f.id });
      await panel.evaluate(() => window.panel.command('furniture', ''));
      await page.waitForFunction(() => window.petDiagnostics?.sceneKey === 'model.glb' && !window.petDiagnostics.loading, { timeout: 20000 });
    }
    console.log('OK:', id, 'anims=', diag.animations?.length, 'furn=', (manifest.furniture || []).length);
  }

  for (const item of fixedChecks) {
    const { character, furniture, shot, freeze } = item;
    await selectChar(character);
    await panel.evaluate((fid) => window.panel.command('furniture', fid), furniture);
    await page.waitForFunction((fid) => window.petDiagnostics?.sceneAction === fid && !window.petDiagnostics.loading && window.petDiagnostics.frames > 5, furniture, { timeout: 25000 });
    assert.equal(await page.evaluate(() => window.petDiagnostics.error), null, `${character}/${furniture}`);
    if (shot) {
      await page.evaluate((t) => { window.petDiagnostics.freezeTime = t; }, freeze);
      await page.waitForTimeout(200);
      await page.screenshot({ path: shot });
      await page.evaluate(() => { delete window.petDiagnostics.freezeTime; });
    }
    if (character === 'saori_dress') {
      const m = await page.evaluate(() => window.petDiagnostics.mirrors);
      assert.ok(Array.isArray(m) && m.length === 1 && m[0].hasMap === true, 'PlanarMirror must be active on saori_dress/f210366_0');
    }
    checked.push({ type: 'fixed-furniture', character, id: furniture });
    await panel.evaluate(() => window.panel.command('furniture', ''));
    await page.waitForFunction(() => window.petDiagnostics?.sceneKey === 'model.glb' && !window.petDiagnostics.loading, { timeout: 20000 });
    console.log('OK FIXED:', character, furniture);
  }

  assert.deepEqual(errors, []);
  writeFileSync('test-results/smoke-v0230.json', JSON.stringify({ exe, checked, errors }, null, 2));
  console.log(`SMOKE TEST PASSED: ${checked.length} checks, 0 errors`);
} finally {
  await app.close();
}
