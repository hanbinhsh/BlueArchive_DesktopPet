import {openTestPanel} from './themed-menu-test-helper.mjs';
import {_electron as electron} from 'playwright';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const specs = JSON.parse(readFileSync('scripts/roster-wave17.json','utf8'));
const ids = process.argv.slice(2).length
  ? process.argv.slice(2)
  : Object.keys(specs).filter(id => existsSync('.assets/wave17-final/' + id + '/character.json'));
const root = path.resolve('.assets/wave17-final');
const profile = path.resolve('test-results/wave17-preview-profile');
mkdirSync(profile, {recursive: true});
writeFileSync(
  path.join(profile, 'settings.json'),
  JSON.stringify({character: ids[0], size: 360, position: {x: 450, y: 180}, eyeFollow: false, allowOffscreen: true})
);
const env = {...process.env, BA_CHARACTERS: root, BA_TEST_DATA: profile};
delete env.ELECTRON_RUN_AS_NODE;
const app = await electron.launch({args: ['.'], env});
const results = [];
try {
  const page = await app.firstWindow();
  const panel = await openTestPanel(app, page);
  await app.evaluate(({BrowserWindow}) => {
    const w = BrowserWindow.getAllWindows().find(w => w.webContents.getURL().endsWith('/index.html'));
    w.setFocusable(false);
    w.setBounds({...w.getBounds(), x: -4000, y: 180});
  });
  await app.evaluate(({screen}) => {
    screen.getCursorScreenPoint = () => ({x: -100000, y: -100000});
  });
  for (const character of ids) {
    if (character !== ids[0]) {
      const loaded = page.waitForEvent('load');
      await panel.evaluate(id => window.panel.command('select', id), character);
      await loaded;
    }
    await page.waitForFunction(() => window.petDiagnostics?.frames > 10 || window.petDiagnostics?.error);
    const diagnostics = await page.evaluate(() => window.petDiagnostics);
    assert.equal(diagnostics.error, null, character);
    await page.screenshot({path: `test-results/wave17-${character}-idle.png`, omitBackground: true});
    const thumb = await page.evaluate(() => {
      const original = document.querySelector('#pet');
      const scratch = document.createElement('canvas');
      scratch.width = original.width;
      scratch.height = original.height;
      const context = scratch.getContext('2d');
      context.drawImage(original, 0, 0);
      const pixels = context.getImageData(0, 0, scratch.width, scratch.height).data;
      let left = scratch.width, top = scratch.height, right = -1, bottom = -1;
      for (let y = 0; y < scratch.height; y++) {
        for (let x = 0; x < scratch.width; x++) {
          if (pixels[(y * scratch.width + x) * 4 + 3] > 16) {
            left = Math.min(left, x);
            top = Math.min(top, y);
            right = Math.max(right, x);
            bottom = Math.max(bottom, y);
          }
        }
      }
      if (right < left) throw Error('Empty character render');
      const target = document.createElement('canvas');
      target.width = 240;
      target.height = 280;
      const w = right - left + 1, h = bottom - top + 1;
      const scale = Math.min(220 / w, 260 / h);
      target.getContext('2d').drawImage(scratch, left, top, w, h, (240 - w * scale) / 2, (280 - h * scale) / 2, w * scale, h * scale);
      return target.toDataURL();
    });
    writeFileSync(path.join(root, character, 'thumbnail.png'), Buffer.from(thumb.split(',')[1], 'base64'));
    results.push({character, diagnostics, thumbnail: true});
    console.log(character, 'rendered');
  }
  writeFileSync('test-results/wave17-preview.json', JSON.stringify(results, null, 2));
} finally {
  await app.close();
}
