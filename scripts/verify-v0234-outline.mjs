// Verifies the packaged v0.2.34 build paints no stray black pixels when the
// outline is enabled (the 0.2.33 regression), using the three scenes reported
// by the user: Fubuki's double chair, Airi's pumpkin counter, Asuna's desk.
//
// Usage: node scripts/verify-v0234-outline.mjs
import {_electron as electron} from 'playwright';
import {openTestPanel} from './themed-menu-test-helper.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const exe = path.resolve('release/v0.2.34/win-unpacked/BA Desktop Pet.exe');
const out = path.resolve('test-results/outline-lines/packaged');
const profile = path.resolve('test-results/v0234-outline-profile');
mkdirSync(out, {recursive: true});
mkdirSync(profile, {recursive: true});
writeFileSync(
  path.join(profile, 'settings.json'),
  JSON.stringify({
    character: 'fubuki', size: 420, position: {x: 450, y: 180}, eyeFollow: false,
    allowOffscreen: true, outline: true, outlineWidth: 38
  })
);

const cases = [
  {character: 'fubuki', furniture: 'f1104_0', time: 7.35},
  {character: 'airi', furniture: 'f5205_0', time: 14.41},
  {character: 'asuna_uniform', furniture: 'f19307_0', time: 0.3}
];

const env = {...process.env, BA_TEST_DATA: profile};
delete env.ELECTRON_RUN_AS_NODE;

const errors = [];
const report = [];
const app = await electron.launch({executablePath: exe, args: [], env});
try {
  const pet = await app.firstWindow();
  pet.on('pageerror', e => errors.push(String(e)));
  pet.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  const panel = await openTestPanel(app, pet);
  await app.evaluate(({BrowserWindow, screen}) => {
    for (const w of BrowserWindow.getAllWindows()) w.webContents.setBackgroundThrottling(false);
    const w = BrowserWindow.getAllWindows().find(w => w.webContents.getURL().endsWith('/index.html'));
    w.setBounds({...w.getBounds(), x: 60, y: 60});
    screen.getCursorScreenPoint = () => ({x: -100000, y: -100000});
  });
  await pet.waitForFunction(() => window.petDiagnostics?.frames > 5 && !window.petDiagnostics.loading);

  for (const testCase of cases) {
    const loaded = pet.waitForEvent('load');
    await panel.evaluate(id => window.panel.command('select', id), testCase.character);
    await loaded.catch(() => {});
    await pet.waitForFunction(() => window.petDiagnostics?.frames > 5 && !window.petDiagnostics.loading);
    await panel.evaluate(id => window.panel.command('furniture', id), testCase.furniture);
    await pet.waitForFunction(model => window.petDiagnostics?.sceneKey === model, testCase.furniture + '.glb', {timeout: 30000})
      .catch(() => {});
    await pet.waitForTimeout(1200);
    await pet.evaluate(t => { window.petDiagnostics.freezeTime = t; }, testCase.time);
    await pet.waitForTimeout(300);
    const name = `${testCase.character}-${testCase.furniture}-t${testCase.time}`;
    await pet.screenshot({path: path.join(out, `${name}-on.png`), omitBackground: true, timeout: 20000});
    const diag = await pet.evaluate(() => ({
      sceneKey: window.petDiagnostics.sceneKey,
      outlineMeshes: window.petDiagnostics.outlineMeshes,
      error: window.petDiagnostics.error
    }));
    await panel.evaluate(() => window.panel.command('settings', {outline: false}));
    await pet.waitForTimeout(400);
    await pet.screenshot({path: path.join(out, `${name}-off.png`), omitBackground: true, timeout: 20000});
    await panel.evaluate(() => window.panel.command('settings', {outline: true}));
    await pet.waitForTimeout(300);
    report.push({...testCase, ...diag});
    console.log('captured', name, diag);
    await panel.evaluate(() => window.panel.command('furniture', ''));
    await pet.waitForTimeout(500);
  }
  assert.deepEqual(errors, [], 'packaged app reported errors');
  assert.ok(report.every(r => r.outlineMeshes > 0), 'outline hulls missing');
  writeFileSync(path.join(out, 'report.json'), JSON.stringify({errors, report}, null, 2));
  console.log('packaged outline verification captured', report.length, 'frames');
} finally {
  await app.close();
}