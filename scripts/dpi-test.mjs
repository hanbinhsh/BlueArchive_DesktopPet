import { _electron as electron } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const root = path.resolve('.');
mkdirSync('test-results', { recursive: true });
const results = [];
for (const factor of [1, 1.5, 2]) {
  const env = { ...process.env, BA_TEST_DATA: path.join(root, 'test-results/dpi-' + factor) }; delete env.ELECTRON_RUN_AS_NODE;
  if (process.env.BA_DPI_CHARACTER) {
    mkdirSync(env.BA_TEST_DATA, {recursive:true});
    writeFileSync(path.join(env.BA_TEST_DATA,'settings.json'), JSON.stringify({character:process.env.BA_DPI_CHARACTER,size:280,position:{x:50,y:50}}));
  }
  const app = await electron.launch({ ...process.env.BA_EXECUTABLE ? {executablePath:process.env.BA_EXECUTABLE,args:['--force-device-scale-factor='+factor]} : {args:['.','--force-device-scale-factor='+factor]}, env });
  try {
    const page = await app.firstWindow();
    await page.waitForFunction(() => window.petDiagnostics?.frames > 5);
    const result = await page.evaluate(() => ({ dpr: devicePixelRatio, width: innerWidth, height: innerHeight, canvasWidth: document.querySelector('canvas').width, canvasHeight: document.querySelector('canvas').height, diagnostics: window.petDiagnostics }));
    assert.equal(result.diagnostics.error, null);
    assert.ok(Math.abs(result.canvasWidth - result.width * factor) <= 1);
    assert.ok(Math.abs(result.canvasHeight - result.height * factor) <= 1);
    await page.screenshot({ path: `test-results/dpi-${factor}.png`, omitBackground: true });
    results.push({ factor, character:(await page.evaluate(()=>window.pet.init())).character.id, executable:process.env.BA_EXECUTABLE||'development', ...result });
  } finally { await app.close(); }
}
writeFileSync(`test-results/dpi${process.env.BA_DPI_CHARACTER?'-'+process.env.BA_DPI_CHARACTER:''}.json`, JSON.stringify(results, null, 2));
console.log(results.map(r => `DPI ${r.factor}: ${r.width}x${r.height}, buffer ${r.canvasWidth}x${r.canvasHeight}`).join('\n'));
