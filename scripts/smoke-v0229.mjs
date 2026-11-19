import {openTestPanel} from './themed-menu-test-helper.mjs';
import {_electron as electron} from 'playwright';
import {mkdirSync, writeFileSync, readFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const specs = JSON.parse(readFileSync('scripts/roster-wave20.json', 'utf8'));
const ids = Object.keys(specs);
const fixedChecks = [
  {character: 'hanae_christmas', furniture: 'f207308_0'},
  {character: 'megu', furniture: 'f6301_0'},
  {character: 'kanna', furniture: 'f207313_0'},
  {character: 'pina_guide', furniture: 'f210368_0'},
];
const exe = path.resolve('release/v0.2.29/win-unpacked/BA Desktop Pet.exe');
const profile = path.resolve('test-results/smoke-v0229-profile');
mkdirSync(profile, {recursive: true});
writeFileSync(
  path.join(profile, 'settings.json'),
  JSON.stringify({character: ids[0], size: 360, position: {x: 450, y: 180}, eyeFollow: false, allowOffscreen: true})
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

  let current = ids[0];
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

  for (const id of ids) {
    await selectChar(id);
    const diag = await page.evaluate(() => window.petDiagnostics);
    checked.push({type: 'character', id, animations: diag.animations?.length || 0});
    const manifest = JSON.parse(readFileSync(`characters/${id}/character.json`, 'utf8'));
    for (const f of manifest.furniture || []) {
      await panel.evaluate(fid => window.panel.command('furniture', fid), f.id);
      await page.waitForFunction(fid => window.petDiagnostics?.sceneAction === fid && !window.petDiagnostics.loading && window.petDiagnostics.frames > 3, f.id, {timeout: 25000});
      assert.equal(await page.evaluate(() => window.petDiagnostics.error), null, `${id}/${f.id}`);
      checked.push({type: 'furniture', character: id, id: f.id});
      await panel.evaluate(() => window.panel.command('furniture', ''));
      await page.waitForFunction(() => window.petDiagnostics?.sceneKey === 'model.glb' && !window.petDiagnostics.loading, {timeout: 20000});
    }
    console.log('OK:', id, 'anims=', diag.animations?.length, 'furn=', (manifest.furniture || []).length);
  }

  for (const {character, furniture} of fixedChecks) {
    await selectChar(character);
    await panel.evaluate(fid => window.panel.command('furniture', fid), furniture);
    await page.waitForFunction(fid => window.petDiagnostics?.sceneAction === fid && !window.petDiagnostics.loading && window.petDiagnostics.frames > 5, furniture, {timeout: 25000});
    assert.equal(await page.evaluate(() => window.petDiagnostics.error), null, `${character}/${furniture}`);
    checked.push({type: 'fixed-furniture', character, id: furniture});
    await panel.evaluate(() => window.panel.command('furniture', ''));
    await page.waitForFunction(() => window.petDiagnostics?.sceneKey === 'model.glb' && !window.petDiagnostics.loading, {timeout: 20000});
    console.log('OK FIXED:', character, furniture);
  }

  assert.deepEqual(errors, []);
  writeFileSync('test-results/smoke-v0229.json', JSON.stringify({exe, checked, errors}, null, 2));
  console.log(`SMOKE TEST PASSED: ${checked.length} checks, 0 errors`);
} finally {
  await app.close();
}
