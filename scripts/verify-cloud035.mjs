import {openTestPanel} from './themed-menu-test-helper.mjs';
import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const profile=path.resolve('test-results/cloud035-profile');mkdirSync(profile,{recursive:true});writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'aris_battle',size:280,playbackSpeed:4,eyeFollow:false,randomIdle:false,roaming:false}));
const env={...process.env,BA_TEST_DATA:profile,BA_CHARACTERS:path.resolve('.assets/fx035-stage')};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({args:['.'],env}),report={loops:0,checks:0,maxDelta:0,samples:[],pause:[],errors:[]};
try{
 const pet=await app.firstWindow();await app.context().setOffline(true);pet.on('pageerror',e=>report.errors.push(String(e)));const panel=await openTestPanel(app,pet);
 await pet.waitForFunction(()=>window.petDiagnostics?.frames>5&&!window.petDiagnostics.loading);
 await app.evaluate(({screen})=>{screen.getCursorScreenPoint=()=>({x:-99999,y:-99999});});
 await panel.evaluate(()=>window.panel.command('furniture','f210394_0'));await pet.waitForFunction(()=>window.petDiagnostics?.sceneAction==='f210394_0'&&!window.petDiagnostics.loading);
 await pet.evaluate(()=>{window.petDiagnostics.measurePose=true;});
 await pet.waitForFunction(()=>Array.isArray(window.petDiagnostics.particleStates));
 let previous;const start=Date.now();
 while(Date.now()-start<21000){
  const d=await pet.evaluate(()=>({time:window.petDiagnostics.actionTime,states:window.petDiagnostics.particleStates?.filter(p=>p.source.includes('retractwindow_BG')),memory:window.petDiagnostics.memory}));
  assert.ok(d.states?.length,'background particle diagnostics missing');report.samples.push(d);
  if(previous&&d.time<previous.time-.1){report.loops++;
   for(const now of d.states){const old=previous.states.find(p=>p.name===now.name);if(now.visible&&old?.visible){const delta=Math.hypot(...now.position.map((v,i)=>v-old.position[i]));report.maxDelta=Math.max(report.maxDelta,delta);assert.ok(delta<.3,`cloud jumps on character loop: ${now.source} ${delta}`);report.checks++;}}
  }
  previous=d;await pet.waitForTimeout(70);
 }
 assert.ok(report.loops>=3&&report.checks>0);
 // Exercise the same suspend/resume notification as the main process.
 await app.evaluate(({powerMonitor})=>powerMonitor.emit('suspend'));await pet.waitForTimeout(150);const before=await pet.evaluate(()=>window.petDiagnostics.actionTime);await pet.waitForTimeout(700);const after=await pet.evaluate(()=>window.petDiagnostics.actionTime);assert.equal(after,before);report.pause=[before,after];
 await app.evaluate(({powerMonitor})=>powerMonitor.emit('resume'));await pet.waitForTimeout(250);assert.notEqual(await pet.evaluate(()=>window.petDiagnostics.actionTime),after);
 assert.deepEqual(report.errors,[]);report.complete=true;
}finally{writeFileSync('test-results/cloud035-runtime.json',JSON.stringify(report,null,2));await app.close();}
console.log(JSON.stringify({complete:report.complete,loops:report.loops,checks:report.checks,maxDelta:report.maxDelta}));
