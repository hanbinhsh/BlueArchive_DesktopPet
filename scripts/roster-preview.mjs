import { _electron as electron } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
const results = [];
for (const character of process.argv.slice(2)) {
  const profile = path.resolve('test-results/roster-preview-profile');
  mkdirSync(profile, { recursive: true });
  writeFileSync(path.join(profile, 'settings.json'), JSON.stringify({ character, size: 420, yaw: 0, alwaysOnTop: true, position: { x: 450, y: 150 } }));
  const env = { ...process.env, BA_TEST_DATA: profile }; delete env.ELECTRON_RUN_AS_NODE;
  const app = await electron.launch({ args: ['.'], env });
  try {
    const page = await app.firstWindow();
    await page.waitForFunction(() => window.petDiagnostics?.frames > 10 || window.petDiagnostics?.error);
    await page.screenshot({ path: `test-results/roster-${character}.png`, omitBackground: true });
    results.push({ character, diagnostics: await page.evaluate(() => window.petDiagnostics) });
  } finally { await app.close(); }
}
writeFileSync('test-results/roster-preview.json', JSON.stringify(results, null, 2));
console.log(JSON.stringify(results, null, 2));
