import * as asar from '@electron/asar';import {writeFileSync} from 'node:fs';import assert from 'node:assert/strict';
const before='release/v0.2.20/win-unpacked/resources/app.asar',after='release/v0.2.21/win-unpacked/resources/app.asar';
const files=asar.listPackage(before).map(p=>p.replaceAll('\\','/')).filter(p=>p.startsWith('/dist/')&&/\.(cjs|js|html|css)$/.test(p));
const identical=[],changed=[];for(const p of files)(asar.extractFile(before,p.slice(1)).equals(asar.extractFile(after,p.slice(1)))?identical:changed).push(p);
assert.deepEqual(changed,['/dist/renderer.js']);
const manifest=JSON.parse(asar.extractFile(after,'package.json'));assert.equal(manifest.version,'0.2.21');
writeFileSync('test-results/release043-program-identity.json',JSON.stringify({version:'0.2.21',baseVersion:'0.2.20',identicalRuntimeFiles:identical,changedRuntimeFiles:changed,reason:'Gated native cauldron trails and camping fire shader; no previous resource enables them.'},null,2));console.log(identical.length,'unchanged program files;',changed);
