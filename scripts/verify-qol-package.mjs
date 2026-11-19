import {extractFile} from '@electron/asar';
import {readFileSync,readdirSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve('release/v0.2.0-final/win-unpacked'),asar=path.join(root,'resources/app.asar');
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const report={complete:false,version:'0.2.0',runtime:[],changedSinceSoak:[],resources:[],native:undefined};
for(const name of readdirSync('dist')){
 const compiled=readFileSync(`dist/${name}`),packed=extractFile(asar,`dist/${name}`);
 assert.deepEqual(packed,compiled,name);report.runtime.push({name,sha256:sha(packed)});
 if(!packed.equals(extractFile('test-results/qol-soak-app.asar',`dist/${name}`)))report.changedSinceSoak.push(name);
}
assert.deepEqual(report.changedSinceSoak,['main.cjs']);
assert.equal(JSON.parse(extractFile(asar,'package.json')).version,report.version);
function* walk(dir,prefix=''){for(const f of readdirSync(dir,{withFileTypes:true})){const name=path.join(prefix,f.name);if(f.isDirectory())yield*walk(path.join(dir,f.name),name);else yield name;}}
for(const name of walk('characters')){const source=readFileSync(path.join('characters',name)),packed=readFileSync(path.join(root,'resources/characters',name));assert.deepEqual(packed,source,name);report.resources.push({name,sha256:sha(packed)});}
const native=readFileSync('native/bin/wheel-forwarder.exe');assert.deepEqual(native,readFileSync(path.join(root,'resources/native/wheel-forwarder.exe')));report.native={name:'wheel-forwarder.exe',sha256:sha(native)};
report.appAsarSha256=sha(readFileSync(asar));report.soakAppAsarSha256=sha(readFileSync('test-results/qol-soak-app.asar'));
report.complete=true;writeFileSync('test-results/qol-release-package.json',JSON.stringify(report,null,2));
console.log({runtime:report.runtime.length,resources:report.resources.length,changedSinceSoak:report.changedSinceSoak,complete:true});
