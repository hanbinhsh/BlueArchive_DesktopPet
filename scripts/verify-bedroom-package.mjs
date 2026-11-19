import {extractFile} from '@electron/asar';
import {readFileSync,readdirSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const file='release/v0.1.22/win-unpacked/resources/app.asar';
const old='release/v0.1.21/win-unpacked/resources/app.asar';
const matched=readdirSync('dist');assert.equal(matched.length,7);
for(const name of matched){
 const data=extractFile(file,`dist/${name}`);
 assert.deepEqual(data,readFileSync(`dist/${name}`));
 assert.deepEqual(data,extractFile(old,`dist/${name}`));
}
assert.equal(JSON.parse(extractFile(file,'package.json')).version,'0.1.22');
writeFileSync('test-results/bedroom-package.json',JSON.stringify({version:'0.1.22',unchangedRuntimeFiles:matched,appAsarSha256:createHash('sha256').update(readFileSync(file)).digest('hex')},null,2));
console.log('All seven compiled runtime files match 0.1.21 and current source build');
