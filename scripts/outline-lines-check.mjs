// Captures outline-on / outline-off screenshots at frozen animation times so a
// solver can tell whether the outline pass paints stray black pixels far away
// from the visible silhouette (the "long black line" bug).
//
// Usage: node scripts/outline-lines-check.mjs <label>
import {_electron as electron} from 'playwright';
import {openTestPanel} from './themed-menu-test-helper.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';

const label = process.argv[2] || 'run';
const out = path.resolve('test-results/outline-lines', label);
const profile = path.resolve('test-results/outline-lines-profile');
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
  {character: 'fubuki', furniture: 'f1104_0'},
  {character: 'airi', furniture: 'f5205_0'},
  {character: 'asuna_uniform', furniture: 'f19307_0'}
];

const env = {...process.env, BA_TEST_DATA: profile};
delete env.ELECTRON_RUN_AS_NODE;

const report = [];
let app = await electron.launch({args: ['.'], env});
try {
  const pet = await app.firstWindow();
  const panel = await openTestPanel(app, pet);
  await app.evaluate(({BrowserWindow, screen}) => {
    for (const w of BrowserWindow.getAllWindows()) w.webContents.setBackgroundThrottling(false);
    const w = BrowserWindow.getAllWindows().find(w => w.webContents.getURL().endsWith('/index.html'));
    w.setBounds({...w.getBounds(), x: 60, y: 60});
    screen.getCursorScreenPoint = () => ({x: -100000, y: -100000});
  });
  pet.setDefaultTimeout(20000);
  pet.on('pageerror', e => report.push({error: String(e)}));
  await pet.waitForFunction(() => window.petDiagnostics?.frames > 5 && !window.petDiagnostics.loading);

  const waitReady = () => pet.waitForFunction(() => window.petDiagnostics?.frames > 5 && !window.petDiagnostics.loading);
  const setFrozen = async time => {
    await pet.evaluate(t => { window.petDiagnostics.freezeTime = t; }, time);
    await pet.waitForTimeout(220);
  };
  const setOutline = async enabled => {
    await panel.evaluate(on => window.panel.command('settings', {outline: on}), enabled);
    await pet.waitForTimeout(320);
  };
  const shot = async (name, outline) => {
    await setOutline(outline);
    await pet.screenshot({path: path.join(out, `${name}-${outline ? 'on' : 'off'}.png`), omitBackground: true, timeout: 15000});
  };
  const capture = async (name, times) => {
    for (const time of times) {
      await setFrozen(time);
      await shot(`${name}-t${time}`, true);
      const diag = await pet.evaluate(() => ({sceneKey: window.petDiagnostics.sceneKey, actionTime: window.petDiagnostics.actionTime, outlineMeshes: window.petDiagnostics.outlineMeshes}));
      await shot(`${name}-t${time}`, false);
      report.push({name, time, ...diag});
    }
    await setOutline(true);
    console.log('captured', name);
  };

  let current = 'fubuki';
  for (const testCase of cases) {
    if (testCase.character !== current) {
      const loaded = pet.waitForEvent('load');
      await panel.evaluate(id => window.panel.command('select', id), testCase.character);
      await loaded;
      await waitReady();
      current = testCase.character;
    }
    // Idle pose first (the user reported the original outfit too).
    await setFrozen(0.5);
    await capture(`${testCase.character}-idle`, [0.5, 2.0]);

    await panel.evaluate(id => window.panel.command('furniture', id), testCase.furniture);
    await pet.waitForFunction(model => window.petDiagnostics?.sceneKey === model, testCase.furniture + '.glb', {timeout: 30000})
      .catch(async () => { await pet.waitForTimeout(3000); });
    await pet.waitForTimeout(1000);
    console.log('furniture ready', testCase.furniture);
    const duration = await pet.evaluate(id => window.petDiagnostics.durations?.['furniture:' + id] || 20, testCase.furniture);
    const step = Math.max(1, (duration - 0.6) / 11);
    const times = [];
    for (let i = 0; i < 12; i++) times.push(Number((0.3 + i * step).toFixed(2)));
    await capture(`${testCase.character}-${testCase.furniture}`, times);

    await panel.evaluate(() => window.panel.command('furniture', ''));
    await pet.waitForTimeout(700);
  }
  writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2));
  console.log('captured', report.filter(r => !r.error).length, 'frames into', out);
} finally {
  await app.close();
}