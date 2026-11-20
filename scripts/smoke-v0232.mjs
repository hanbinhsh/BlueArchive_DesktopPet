import { openTestPanel } from './themed-menu-test-helper.mjs';
import { _electron as electron } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const exe = path.resolve('release/v0.2.32/win-unpacked/BA Desktop Pet.exe');
const profile = path.resolve('test-results/smoke-v0232-profile');
mkdirSync(profile, { recursive: true });
writeFileSync(
  path.join(profile, 'settings.json'),
  JSON.stringify({ character: 'yuzu_maid', size: 360, position: { x: 450, y: 180 }, eyeFollow: false, allowOffscreen: true, outline: true, pitch: 0.15 }),
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

  await page.waitForFunction(() => window.petDiagnostics?.frames > 5 && !window.petDiagnostics.loading, { timeout: 20000 });
  assert.equal(await page.evaluate(() => window.petDiagnostics.error), null, 'yuzu_maid idle');
  checked.push('yuzu_maid:idle');

  const actions = [
    'interact',
    'walk',
    'pickup',
    'original_exs',
    'original_tactical_start',
    'original_exs_cutin_genryumon_ar',
    'original_exs_cutin_genryumon_hg',
    'original_b_st_attack_ing',
  ];
  for (const aid of actions) {
    await panel.evaluate((id) => window.panel.command('action', id), aid);
    await page.waitForTimeout(220);
    assert.equal(await page.evaluate(() => window.petDiagnostics.error), null, `yuzu_maid:${aid}`);
    assert.equal(await page.evaluate(() => window.petDiagnostics.action), aid, `active action ${aid}`);
    checked.push(`yuzu_maid:${aid}`);
    console.log('OK:', aid);
  }

  // Also test furniture f210304_0
  await panel.evaluate(() => window.panel.command('furniture', 'f210304_0'));
  await page.waitForFunction(() => window.petDiagnostics?.sceneAction === 'f210304_0' && !window.petDiagnostics.loading && window.petDiagnostics.frames > 3, { timeout: 25000 });
  assert.equal(await page.evaluate(() => window.petDiagnostics.error), null, 'yuzu_maid/f210304_0');
  checked.push('yuzu_maid:f210304_0');
  console.log('OK: f210304_0');

  assert.deepEqual(errors, []);
  writeFileSync('test-results/smoke-v0232.json', JSON.stringify({ exe, checked, errors }, null, 2));
  console.log(`SMOKE TEST PASSED: ${checked.length} checks, 0 errors`);
} finally {
  await app.close();
}
