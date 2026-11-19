import {openTestPanel} from './themed-menu-test-helper.mjs';
import {_electron as electron} from 'playwright';
import {mkdirSync, writeFileSync, readFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const exe = path.resolve('release/v0.2.27/win-unpacked/BA Desktop Pet.exe');
const profile = path.resolve('test-results/smoke-v0227-profile');
mkdirSync(profile, {recursive: true});
writeFileSync(
  path.join(profile, 'settings.json'),
  JSON.stringify({character: 'renge', size: 360, position: {x: 450, y: 180}, eyeFollow: false, allowOffscreen: true})
);

const env = {...process.env, BA_TEST_DATA: profile};
delete env.ELECTRON_RUN_AS_NODE;

const app = await electron.launch({executablePath: exe, args: [], env});
const errors = [];
const checked = [];

try {
  const page = await app.firstWindow();
  await app.context().setOffline(true);
  page.on('pageerror', e => { errors.push('PAGEERROR: ' + String(e)); console.error('PAGEERROR', e); });
  page.on('console', e => { if (e.type() === 'error') { errors.push('CONSOLE: ' + e.text()); console.error('CONSOLE', e.text()); } });

  const panel = await openTestPanel(app, page);
  await app.evaluate(({BrowserWindow}) => {
    const w = BrowserWindow.getAllWindows().find(w => w.webContents.getURL().endsWith('/index.html'));
    w.setFocusable(false);
    w.setBounds({...w.getBounds(), x: -4000, y: 180});
  });

  let current = 'renge';
  const selectChar = async (id) => {
    if (current !== id) {
      const loaded = page.waitForEvent('load');
      await panel.evaluate(x => window.panel.command('select', x), id);
      await loaded;
      current = id;
    }
    await page.waitForFunction(() => window.petDiagnostics?.frames > 5 && !window.petDiagnostics.loading, {timeout: 20000});
    assert.equal(await page.evaluate(() => window.petDiagnostics.error), null, id);
  };

  // 1. Check all 10 new outfits
  for (const id of ['renge', 'renge_swimsuit', 'makoto', 'makoto_swimsuit', 'noa', 'noa_pajama', 'himari', 'himari_battle', 'yukino', 'np0283']) {
    await selectChar(id);
    const diag = await page.evaluate(() => window.petDiagnostics);
    checked.push({type: 'character', id, animations: diag.animations?.length || 0});
    console.log('OK char:', id, 'anims=', diag.animations?.length);
  }

  // 2. Check toki 25 actions & restored actions
  await selectChar('toki');
  const tokiDiag = await page.evaluate(() => window.petDiagnostics);
  assert.equal(tokiDiag.animations.length, 25, 'Expected 25 actions on toki');
  await panel.evaluate(() => window.panel.command('action', 'original_exs01'));
  await page.waitForTimeout(250);
  assert.equal(await page.evaluate(() => window.petDiagnostics.error), null, 'toki original_exs01');
  checked.push({type: 'toki-restored', actions: tokiDiag.animations.length});
  console.log('OK toki: 25 actions + original_exs01 played cleanly');

  // 3. Check representative Wave 18 Cafe + Field-Cafe furniture scenes
  const scenes = [
    ['renge', 'f210325_0'],
    ['makoto', 'f210331_0'],
    ['noa_pajama', 'f210357_0'],
    ['himari_battle', 'f210392_0'],
    ['hina', 'field_bookshelf_ing'],
    ['hina', 'field_cat_ing'],
    ['hina', 'field_piano_ing'],
    ['hina_dress', 'field_table_ing'],
    ['seia', 'field_gymball_ing'],
    ['seia', 'field_mic_ing'],
    ['seia', 'field_cabinet_ing'],
    ['seia', 'field_vending01_ing'],
    ['seia', 'field_riosbot_ing'],
    ['np0283', 'field_cat_ing'],
    ['np0283', 'field_bench_ing'],
  ];

  for (const [ch, fid] of scenes) {
    await selectChar(ch);
    await panel.evaluate(id => window.panel.command('furniture', id), fid);
    await page.waitForFunction(id => window.petDiagnostics?.sceneAction === id && !window.petDiagnostics.loading && window.petDiagnostics.frames > 3, fid, {timeout: 20000});
    assert.equal(await page.evaluate(() => window.petDiagnostics.error), null, `${ch}/${fid}`);
    checked.push({type: 'furniture', character: ch, id: fid});
    console.log('OK furn:', ch, fid);
    await panel.evaluate(() => window.panel.command('furniture', ''));
    await page.waitForFunction(() => window.petDiagnostics?.sceneKey === 'model.glb' && !window.petDiagnostics.loading, {timeout: 20000});
  }

  assert.deepEqual(errors, []);
  writeFileSync('test-results/smoke-v0227.json', JSON.stringify({exe, checked, errors}, null, 2));
  console.log(`SMOKE TEST PASSED: ${checked.length} checks, 0 errors`);
} finally {
  await app.close();
}
