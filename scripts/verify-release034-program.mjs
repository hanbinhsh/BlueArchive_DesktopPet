// Confirms v0.2.34 changed only the renderer among packaged runtime files.
import * as asar from '@electron/asar';
import {writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';

const before = 'release/v0.2.33/win-unpacked/resources/app.asar';
const after = 'release/v0.2.34/win-unpacked/resources/app.asar';
const files = asar.listPackage(after).map(p => p.replaceAll('\\', '/')).filter(p => p.startsWith('/dist/') && /\.(cjs|js|html|css)$/.test(p));
const identical = [], changed = [];
for (const p of files) {
  (asar.extractFile(before, p.slice(1)).equals(asar.extractFile(after, p.slice(1))) ? identical : changed).push(p);
}
assert.deepEqual(changed, ['/dist/renderer.js']);
const manifest = JSON.parse(asar.extractFile(after, 'package.json'));
assert.equal(manifest.version, '0.2.34');
writeFileSync('test-results/release034-program-identity.json', JSON.stringify({
  version: '0.2.34', baseVersion: '0.2.33', identicalRuntimeFiles: identical, changedRuntimeFiles: changed
}, null, 2));
console.log(identical.length, 'unchanged runtime files;', changed);