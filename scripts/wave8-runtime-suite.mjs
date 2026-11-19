import {spawn} from 'node:child_process';
import {readFileSync,writeFileSync,copyFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const ids=Object.keys(JSON.parse(readFileSync('.assets/wave8-all-specs.json','utf8')));
const results=[];
for(const [script,report] of [['wave8-panel-test.mjs','wave8-panel'],['hold-test.mjs','hold'],['transitions-test.mjs','transitions-packaged'],['expressions-test.mjs','expressions']]){
 if(report==='wave8-panel'&&process.argv.includes('--continue-after-panel')){
  const checked=JSON.parse(readFileSync('test-results/wave8-panel.json','utf8'));
  assert.equal(checked.executable,process.env.BA_EXECUTABLE);assert.equal(checked.results.length,16);assert.deepEqual(checked.errors,[]);
  results.push({script,exitCode:0,executable:process.env.BA_EXECUTABLE,priorCompleted:true});continue;
 }
 const exitCode=await new Promise((resolve,reject)=>{const p=spawn(process.execPath,[`scripts/${script}`,...ids],{env:process.env,stdio:'inherit',windowsHide:true});p.once('error',reject);p.once('exit',resolve);});
 results.push({script,exitCode,executable:process.env.BA_EXECUTABLE});
 writeFileSync('test-results/wave8-runtime-suite.json',JSON.stringify(results,null,2));
 assert.equal(exitCode,0,script);
 if(report!=='wave8-panel')copyFileSync(`test-results/${report}.json`,`test-results/wave8-${report==='transitions-packaged'?'transitions':report}.json`);
}
