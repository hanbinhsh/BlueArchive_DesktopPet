import * as asar from '@electron/asar';import {writeFileSync} from 'node:fs';import assert from 'node:assert/strict';
const before='release/v0.2.19/win-unpacked/resources/app.asar',after='release/v0.2.20/win-unpacked/resources/app.asar';
const files=asar.listPackage(before).map(p=>p.replaceAll('\\','/')).filter(p=>p.startsWith('/dist/')&&/\.(cjs|js|html|css)$/.test(p));
assert.equal(files.length,15);for(const p of files)assert.ok(asar.extractFile(before,p.slice(1)).equals(asar.extractFile(after,p.slice(1))),p);
writeFileSync('test-results/release042-program-identity.json',JSON.stringify({version:'0.2.20',baseVersion:'0.2.19',identicalRuntimeFiles:files},null,2));console.log('All 15 program runtime files unchanged');
