import {extractFile} from '@electron/asar';
import {readFileSync,readdirSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const file='release/v0.1.21/win-unpacked/resources/app.asar';
const baseline='release/v0.1.20/win-unpacked/resources/app.asar';
const matchedBuiltFiles=readdirSync('dist');assert.equal(matchedBuiltFiles.length,7);
const changed=[];
for(const name of matchedBuiltFiles){
 const built=extractFile(file,`dist/${name}`);assert.deepEqual(built,readFileSync(`dist/${name}`));
 if(!built.equals(extractFile(baseline,`dist/${name}`)))changed.push(name);
}
assert.deepEqual(changed,['panel.js']);
assert.equal(JSON.parse(extractFile(file,'package.json')).version,'0.1.21');
writeFileSync('test-results/panel-scroll-package.json',JSON.stringify({version:'0.1.21',matchedBuiltFiles,changed,appAsarSha256:createHash('sha256').update(readFileSync(file)).digest('hex')},null,2));
console.log('Only panel.js changed; all seven compiled files match the package');
