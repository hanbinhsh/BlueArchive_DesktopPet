import { _electron as electron } from 'playwright';
import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';

const env = { ...process.env, BA_TEST_DATA: path.resolve('test-results/move-profile') };
delete env.ELECTRON_RUN_AS_NODE;
mkdirSync(env.BA_TEST_DATA, { recursive: true });
const app = await electron.launch({ args: ['.'], env });
try {
  const page = await app.firstWindow();
  await page.waitForFunction(() => window.petDiagnostics?.frames > 5);
  const retained = await page.evaluate(() => {
    const canvas = document.querySelector('canvas');
    const gl = canvas.getContext('webgl2');
    window.canvasChanges = 0;
    new MutationObserver(records => { window.canvasChanges += records.length; })
      .observe(canvas, { attributes: true, attributeFilter: ['width', 'height'] });
    window.opaquePixels = () => {
      const pixels = new Uint8Array(gl.drawingBufferWidth * gl.drawingBufferHeight * 4);
      gl.readPixels(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
      let count = 0;
      for (let i = 3; i < pixels.length; i += 4) if (pixels[i] > 128) count++;
      return count;
    };
    return gl.getContextAttributes().preserveDrawingBuffer;
  });
  assert.equal(retained, true);
  // Pause new draws while retaining the visible window: DWM must still have a
  // complete frame when moving between draws at the normal 30 FPS limit.
  await app.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].webContents.send('pet:visibility', false));
  await page.waitForTimeout(100);
  const samples = [];
  for (let i = 0; i < 60; i++) {
    await app.evaluate(({ BrowserWindow }, i) => BrowserWindow.getAllWindows()[0].setPosition(300 + i * 3, 200 + Math.round(Math.sin(i / 5) * 30), false), i);
    samples.push(await page.evaluate(() => {
      window.dispatchEvent(new Event('resize'));
      return window.opaquePixels();
    }));
    await page.waitForTimeout(16);
  }
  const changes = await page.evaluate(() => window.canvasChanges);
  assert.equal(changes, 0, 'Movement must not reallocate the drawing buffer');
  assert.ok(Math.min(...samples) > 1000, 'The model frame must remain available between draws');
  await app.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].webContents.send('pet:visibility', true));
  await page.waitForTimeout(300);
  const result = { retained, canvasReallocations: changes, samples: samples.length, minimumOpaquePixels: Math.min(...samples), error: await page.evaluate(() => window.petDiagnostics.error) };
  assert.equal(result.error, null);
  writeFileSync('test-results/move-render.json', JSON.stringify(result, null, 2));
  console.log(result);
} finally { await app.close(); }
