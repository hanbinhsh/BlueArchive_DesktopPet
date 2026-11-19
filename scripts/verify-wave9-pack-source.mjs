import {extractFile} from '@electron/asar';
import {readFileSync,readdirSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const file='release/v0.1.20/win-unpacked/resources/app.asar';
const baseline='release/v0.1.19/win-unpacked/resources/app.asar';
const matchedBuiltFiles=readdirSync('dist');assert.equal(matchedBuiltFiles.length,7);
for(const name of matchedBuiltFiles){
 const built=extractFile(file,`dist/${name}`);
 assert.deepEqual(built,readFileSync(`dist/${name}`));
 assert.deepEqual(built,extractFile(baseline,`dist/${name}`));
}
const version=JSON.parse(extractFile(file,'package.json')).version;assert.equal(version,'0.1.20');
writeFileSync('test-results/wave9-pack-source.json',JSON.stringify({version,matchedBuiltFiles,unchangedRuntimeFrom:'0.1.19',appAsarSha256:createHash('sha256').update(readFileSync(file)).digest('hex')},null,2));
console.log('Seven built files match the package and the previous release runtime');
