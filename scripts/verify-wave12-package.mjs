import {extractFile} from '@electron/asar';
import {readFileSync,readdirSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve('release/v0.2.3/win-unpacked'),asar=path.join(root,'resources/app.asar'),previous='release/v0.2.2/win-unpacked/resources/app.asar';
const hash=buffer=>createHash('sha256').update(buffer).digest('hex');
const report={version:'0.2.3',complete:false,runtime:[],unchangedRuntime:[],assets:0};
for(const name of readdirSync('dist')){const bytes=extractFile(asar,`dist/${name}`);assert.deepEqual(bytes,readFileSync(`dist/${name}`));report.runtime.push(name);try{if(bytes.equals(extractFile(previous,`dist/${name}`)))report.unchangedRuntime.push(name);}catch{/* Newly added popup files. */}}
assert.equal(report.runtime.length,15);
assert.equal(JSON.parse(extractFile(asar,'package.json')).version,report.version);
function* walk(dir,prefix=''){for(const f of readdirSync(dir,{withFileTypes:true})){const key=path.join(prefix,f.name);if(f.isDirectory())yield*walk(path.join(dir,f.name),key);else yield key;}}
for(const name of walk('characters')){assert.deepEqual(readFileSync(path.join(root,'resources/characters',name)),readFileSync(path.join('characters',name)),name);report.assets++;}
assert.equal(report.assets,534);assert.deepEqual(readFileSync(path.join(root,'resources/native/wheel-forwarder.exe')),readFileSync('native/bin/wheel-forwarder.exe'));
report.appAsarSha256=hash(readFileSync(asar));report.complete=true;writeFileSync('test-results/wave12-package.json',JSON.stringify(report,null,2));console.log(report);
