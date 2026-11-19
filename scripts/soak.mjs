import { _electron as electron } from 'playwright';
import { mkdirSync, appendFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const root = path.resolve('.');
const executablePath = process.env.BA_EXECUTABLE;
const minutes = Number(process.env.BA_SOAK_MINUTES || 30);
mkdirSync('test-results', { recursive: true });
writeFileSync('test-results/soak-samples.jsonl', '');
const env = { ...process.env, BA_TEST_DATA: path.join(root, 'test-results/soak-profile') };
if(process.env.BA_SOAK_CHARACTER){
 mkdirSync(env.BA_TEST_DATA,{recursive:true});
 writeFileSync(path.join(env.BA_TEST_DATA,'settings.json'),JSON.stringify({character:process.env.BA_SOAK_CHARACTER,size:280,position:{x:20,y:20},alwaysOnTop:true}));
}
delete env.ELECTRON_RUN_AS_NODE;
const app = await electron.launch({ ...(executablePath ? { executablePath, args: [] } : { args: ['.'] }), env });
const started = Date.now();
const samples = [];
let page;
try {
  page = await app.firstWindow();
  await page.waitForFunction(() => window.petDiagnostics?.frames > 5);
  if(process.env.BA_SOAK_BACKGROUND)await app.evaluate(({BrowserWindow,screen})=>{
    BrowserWindow.getAllWindows()[0].setFocusable(false);
    screen.getCursorScreenPoint=()=>({x:-100000,y:-100000});
  });
  // Simulate offline operation without altering the computer's network.
  await app.context().setOffline(true);
  await page.reload();
  await page.waitForFunction(() => window.petDiagnostics?.frames > 5);
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  while (Date.now() - started < minutes * 60000) {
    await new Promise(resolve => setTimeout(resolve, 10000));
    const diagnostics = await page.evaluate(() => window.petDiagnostics);
    assert.equal(diagnostics.error, null);
    const metrics = await app.evaluate(({ app }) => app.getAppMetrics().map(p => ({ type: p.type, cpu: p.cpu.percentCPUUsage, memoryKB: p.memory.workingSetSize })));
    const sample = { elapsedSeconds: (Date.now() - started) / 1000, diagnostics, metrics };
    samples.push(sample); appendFileSync('test-results/soak-samples.jsonl', JSON.stringify(sample) + '\n');
    if (samples.length % 6 === 0) console.log(`Soak: ${Math.round(sample.elapsedSeconds / 60)} min, frames=${diagnostics.frames}, memory=${Math.round(metrics.reduce((a, p) => a + p.memoryKB, 0) / 1024)} MiB`);
  }
  const stable = samples.filter(s => s.elapsedSeconds >= Math.min(120, minutes * 60 / 4));
  const total = s => s.metrics.reduce((a, p) => a + p.memoryKB, 0) / 1024;
  const first = stable[0], last = stable.at(-1);
  const fps = (last.diagnostics.frames - first.diagnostics.frames) / (last.elapsedSeconds - first.elapsedSeconds);
  const summary = { minutes, character:process.env.BA_SOAK_CHARACTER||'saved/default', executablePath: executablePath || 'development', offlineReload: true, elapsedSeconds: (Date.now() - started) / 1000, fps, memoryMiB: { first: total(first), final: total(last), min: Math.min(...stable.map(total)), max: Math.max(...stable.map(total)) }, rendererErrors: errors, samples: samples.length };
  await page.screenshot({ path: 'test-results/soak-final.png', omitBackground: true });
  writeFileSync('test-results/soak-summary.json', JSON.stringify(summary, null, 2));
  assert.deepEqual(errors, []);
  assert.ok(fps > 20 && fps <= 32, `Unexpected FPS: ${fps}`);
  assert.ok(total(last) - total(first) < 100, 'Memory grew by over 100 MiB after warmup');
  console.log(JSON.stringify(summary, null, 2));
} finally { await app.close(); }
