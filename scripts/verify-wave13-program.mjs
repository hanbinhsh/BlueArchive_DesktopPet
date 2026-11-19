import * as asar from '@electron/asar';
import {writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const old='release/v0.2.17/win-unpacked/resources/app.asar',current='release/v0.2.18/win-unpacked/resources/app.asar';
const files=asar.listPackage(old).map(p=>p.replaceAll('\\','/')).filter(p=>p.startsWith('/dist/')&&/\.(cjs|js|html|css)$/.test(p));assert.ok(files.length>=14);
for(const file of files)assert.ok(asar.extractFile(old,file.slice(1)).equals(asar.extractFile(current,file.slice(1))),file);
writeFileSync('test-results/wave13-program-identity.json',JSON.stringify({baseVersion:'0.2.17',version:'0.2.18',identicalRuntimeFiles:files},null,2));
console.log('Unchanged runtime files:',files.length);
