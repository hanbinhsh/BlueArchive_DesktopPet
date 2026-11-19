import { _electron as electron } from 'playwright';
import { mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const root = path.resolve('.');
const manifest = JSON.parse(readFileSync('characters/serika/character.json', 'utf8'));
const model = readFileSync('characters/serika/model.glb');
const checks = [];
for (const kind of ['corrupt-model', 'missing-animation', 'invalid-settings']) {
  const profile = path.join(root, 'test-results', kind + '-profile');
  const packs = path.join(root, 'test-results', kind + '-characters');
  mkdirSync(profile, { recursive: true }); mkdirSync(path.join(packs, 'serika'), { recursive: true });
  writeFileSync(path.join(profile, 'settings.json'), kind === 'invalid-settings' ? '{bad json' : '{}');
  const copy = structuredClone(manifest);
  if (kind === 'missing-animation') {
    copy.animations.interact = 'does-not-exist';
    copy.actions.find(a => a.id === 'interact').clip = 'does-not-exist';
  }
  writeFileSync(path.join(packs, 'serika/character.json'), JSON.stringify(copy));
  writeFileSync(path.join(packs, 'serika/model.glb'), kind === 'corrupt-model' ? 'broken GLB' : model);
  const env = { ...process.env, BA_TEST_DATA: profile, BA_CHARACTERS: packs }; delete env.ELECTRON_RUN_AS_NODE;
  const app = await electron.launch({ args: ['.'], env });
  try {
    const page = await app.firstWindow();
    await page.waitForFunction(() => window.petDiagnostics && (window.petDiagnostics.error || window.petDiagnostics.frames > 5));
    const diagnostics = await page.evaluate(() => window.petDiagnostics);
    if (kind === 'invalid-settings') {
      assert.equal(diagnostics.error, null);
      assert.equal((await page.evaluate(async () => (await window.pet.init()).settings)).size, 280);
    } else {
      assert.match(diagnostics.error, kind === 'corrupt-model' ? /GLB 文件损坏/ : /缺少独立的待机或互动动画/);
      assert.ok(await page.locator('#status').isVisible());
    }
    checks.push({ kind, diagnostics });
  } finally { await app.close(); }
}
writeFileSync('test-results/failure-cases.json', JSON.stringify(checks, null, 2));
console.log(checks.map(c => c.kind + ': passed').join('\n'));
