import { _electron as electron } from 'playwright';
import { mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const profile = path.resolve('test-results/costumes-profile');
mkdirSync(profile, { recursive: true });
writeFileSync(path.join(profile, 'settings.json'), JSON.stringify({ character: 'serika', size: 360, yaw: 0, alwaysOnTop: true, position: { x: 500, y: 200 } }));
const env = { ...process.env, BA_TEST_DATA: profile }; delete env.ELECTRON_RUN_AS_NODE;
const launch = () => electron.launch({ ...(process.env.BA_EXECUTABLE ? { executablePath: path.resolve(process.env.BA_EXECUTABLE), args: [] } : { args: ['.'] }), env });
let app = await launch();
const checks = [];
try {
  let page = await app.firstWindow();
  await page.waitForFunction(() => window.petDiagnostics?.frames > 5);
  await app.evaluate(({ Menu }) => { Menu.prototype.popup = function () { globalThis.costumeTestMenu = this; }; });
  async function menu(id) {
    await page.evaluate(() => window.pet.menu());
    await app.evaluate(({ BrowserWindow }, id) => {
      const item = globalThis.costumeTestMenu.getMenuItemById(id);
      assertMenuItem(item);
      function assertMenuItem(item) { if (!item) throw new Error('Missing menu item ' + id); }
      item.click(item, BrowserWindow.getAllWindows()[0], {});
    }, id);
  }
  for (const costume of ['serika', 'serika_newyear']) {
    if (costume !== 'serika') {
      const loaded = page.waitForEvent('load');
      await menu(`costume-${costume}`); await loaded;
      await page.waitForFunction(() => window.petDiagnostics?.frames > 5);
    }
    const init = await page.evaluate(() => window.pet.init());
    assert.equal(init.character.id, costume);
    await page.evaluate(() => window.pet.menu());
    const actionCount = await app.evaluate(() => globalThis.costumeTestMenu.items.find(i => i.label === '动作').submenu.items.length);
    assert.equal(actionCount, costume === 'serika' ? 6 : 4);
    const defaultMouth = costume === 'serika' ? 402 : 704;
    assert.equal(await page.evaluate(() => window.petDiagnostics.mouthTile), defaultMouth);
    await page.screenshot({ path: `test-results/costume-${costume}.png`, omitBackground: true });
    await menu('action-interact');
    await page.waitForFunction(() => window.petDiagnostics.action === 'interact');
    await page.waitForTimeout(700);
    await page.screenshot({ path: `test-results/costume-${costume}-interact.png`, omitBackground: true });
    await page.waitForFunction(() => window.petDiagnostics.action === 'idle', null, { timeout: 25000 });
    // Locate a hittable model pixel rather than assuming identical costumes.
    let found = false;
    for (let y = 140; y <= 300 && !found; y += 20) {
      await page.mouse.move(270, y); await page.waitForTimeout(40);
      found = await page.evaluate(() => window.petDiagnostics.hit);
    }
    assert.ok(found, 'Model must accept pointer input');
    await page.mouse.down();
    // Screen delta above 4 px begins movement, not a click or rotation.
    await page.mouse.move(285, 200, { steps: 3 });
    await page.waitForFunction(() => window.petDiagnostics.action === 'pickup');
    await page.waitForTimeout(800);
    await page.screenshot({ path: `test-results/costume-${costume}-drag.png`, omitBackground: true });
    await page.waitForTimeout(costume === 'serika_newyear' ? 17000 : 4000);
    assert.equal(await page.evaluate(() => window.petDiagnostics.action), 'pickup');
    await page.screenshot({ path: `test-results/costume-${costume}-held.png`, omitBackground: true });
    await page.mouse.up();
    await page.waitForFunction(() => window.petDiagnostics.action === 'idle');
    assert.equal(await page.evaluate(() => window.petDiagnostics.mouthTile), defaultMouth);
    assert.equal(await page.evaluate(() => window.petDiagnostics.error), null);
    checks.push(`${costume}: idle, original mouth interaction, drag pickup, long hold, release to idle`);
  }
  await page.waitForTimeout(300); await app.close();
  assert.equal(JSON.parse(readFileSync(path.join(profile, 'settings.json'))).character, 'serika_newyear');
  app = await launch(); page = await app.firstWindow();
  await page.waitForFunction(() => window.petDiagnostics?.frames > 5);
  assert.equal(await page.evaluate(async () => (await window.pet.init()).character.id), 'serika_newyear');
  checks.push('Restart restores selected costume');
  writeFileSync('test-results/costumes.json', JSON.stringify({ checks }, null, 2));
  console.log(checks.join('\n'));
} finally { await app.close(); }
