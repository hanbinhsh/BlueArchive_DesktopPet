import {openTestPanel} from './themed-menu-test-helper.mjs';
import {_electron as electron} from 'playwright';
import {writeFileSync, mkdirSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const exe = path.resolve(process.env.BA_EXECUTABLE || 'release/v0.2.25/win-unpacked/BA Desktop Pet.exe');
const profile = path.resolve('test-results/release046-smoke-profile');
mkdirSync(profile, {recursive: true});
writeFileSync(
  path.join(profile, 'settings.json'),
  JSON.stringify({character: 'haruka_dress', size: 360, position: {x: 450, y: 180}, eyeFollow: false, allowOffscreen: true})
);
const env = {...process.env, BA_TEST_DATA: profile};
delete env.ELECTRON_RUN_AS_NODE;

const checks = [
  ['haruka_dress', 'f15300_0'],
  ['erina', 'f211317_0'],
  ['chihiro', 'f2203_0'],
  ['nonomi_swimsuit', 'f4108_0'],
  ['ako_dress', 'f15306_1'],
  ['utaha_cheerleader', 'f10302_0'],
  ['hibiki_cheerleader', 'f10302_0'],
  ['yukari_swimsuit', 'f13302_0'],
  ['minori', 'f210307_0'],
  ['yuzu_battle', 'f23112_0'],
  ['kasumi', 'f9106_0'],
  ['nodoka_onsen', 'f6201_0'],
  ['tomoe', 'f6100_0'],
  ['ibuki_swimsuit', 'f211311_0'],
];

const app = await electron.launch({executablePath: exe, args: [], env});
const errors = [];
const results = [];
try {
  const page = await app.firstWindow();
  await app.context().setOffline(true);
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', e => { if (e.type() === 'error') errors.push(e.text()); });
  const panel = await openTestPanel(app, page);
  await app.evaluate(({BrowserWindow}) => {
    const w = BrowserWindow.getAllWindows().find(w => w.webContents.getURL().endsWith('/index.html'));
    w.setFocusable(false);
    w.setBounds({...w.getBounds(), x: -4000, y: 180});
  });
  await app.evaluate(({screen}) => {
    screen.getCursorScreenPoint = () => ({x: -100000, y: -100000});
  });
  const state = await panel.evaluate(() => window.panel.state());
  console.log('Packaged roster count:', state.characters.length);
  assert.equal(state.characters.length, 224, 'Expected 224 installed outfits in packaged exe');
  let selected = 'haruka_dress';
  for (const [character, fid] of checks) {
    if (selected !== character) {
      const loaded = page.waitForEvent('load');
      await panel.evaluate(id => window.panel.command('select', id), character);
      await loaded;
      selected = character;
    }
    await page.waitForFunction(() => window.petDiagnostics?.frames > 5 && !window.petDiagnostics.loading);
    assert.equal(await page.evaluate(() => window.petDiagnostics.error), null, character);
    await panel.evaluate(id => window.panel.command('furniture', id), fid);
    await page.waitForFunction(id => window.petDiagnostics?.sceneAction === id && !window.petDiagnostics.loading, fid, {timeout: 25000});
    assert.equal(await page.evaluate(() => window.petDiagnostics.error), null, `${character}/${fid}`);
    await page.evaluate(t => { window.petDiagnostics.freezeTime = t; }, 3.0);
    await page.waitForTimeout(120);
    const diag = await page.evaluate(() => window.petDiagnostics);
    results.push({character, furniture: fid, sceneKey: diag.sceneKey, frames: diag.frames});
    console.log('OK', character, fid);
    await page.evaluate(() => { delete window.petDiagnostics.freezeTime; });
    await panel.evaluate(() => window.panel.command('furniture', ''));
    await page.waitForFunction(() => window.petDiagnostics?.sceneKey === 'model.glb' && !window.petDiagnostics.loading);
  }
  assert.deepEqual(errors, [], `Runtime errors: ${errors.join('; ')}`);
  writeFileSync('test-results/release046-smoke.json', JSON.stringify({rosterCount: state.characters.length, results, errors}, null, 2));
  console.log('PACKAGED EXE SMOKE TEST PASSED: 224 outfits, 14 scenes verified, 0 errors');
} finally {
  await app.close();
}
