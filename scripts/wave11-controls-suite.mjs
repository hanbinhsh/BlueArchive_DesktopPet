import {spawn} from 'node:child_process';
import {readFileSync,writeFileSync,copyFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const ids=Object.keys(JSON.parse(readFileSync('scripts/roster-wave11.json','utf8'))),rows=[];
for(const [script,source,label] of [['hold-test.mjs','hold.json','hold'],['transitions-test.mjs',process.env.BA_EXECUTABLE?'transitions-packaged.json':'transitions-ui.json','transitions']]){
 const code=await new Promise((resolve,reject)=>{const child=spawn(process.execPath,[`scripts/${script}`,...ids],{env:process.env,stdio:'inherit',windowsHide:true});child.once('error',reject);child.once('exit',resolve);});
 assert.equal(code,0,script);const report=JSON.parse(readFileSync(`test-results/${source}`,'utf8'));assert.deepEqual(report.map(r=>r.character).sort(),[...ids].sort());copyFileSync(`test-results/${source}`,`test-results/wave11-${label}.json`);rows.push({script,passed:true,executable:process.env.BA_EXECUTABLE});writeFileSync('test-results/wave11-controls-suite.json',JSON.stringify(rows,null,2));
}
