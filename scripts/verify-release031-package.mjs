import {extractFile} from '@electron/asar';
import {readFileSync,readdirSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const base='release/v0.2.11/win-unpacked',asar=`${base}/resources/app.asar`;
const report={version:'0.2.11',complete:false,runtime:[]};
for(const name of readdirSync('dist')){
 assert.deepEqual(extractFile(asar,`dist/${name}`),readFileSync(`dist/${name}`),name);
 report.runtime.push(name);
}
assert.equal(report.runtime.length,15);
assert.equal(JSON.parse(extractFile(asar,'package.json')).version,report.version);
assert.deepEqual(readFileSync(`${base}/resources/native/wheel-forwarder.exe`),readFileSync('native/bin/wheel-forwarder.exe'));
report.appAsarSha256=createHash('sha256').update(readFileSync(asar)).digest('hex');
report.complete=true;
writeFileSync('test-results/release031-verification.json',JSON.stringify(report,null,2));
console.log(report);
