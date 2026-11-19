import {openTestPanel} from './themed-menu-test-helper.mjs';
import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const profile=path.resolve('test-results/water038-profile');mkdirSync(profile,{recursive:true});writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'eimi_swimsuit',size:280,playbackSpeed:4,eyeFollow:false,randomIdle:false,roaming:false}));
const env={...process.env,BA_TEST_DATA:profile,BA_CHARACTERS:path.resolve(process.env.BA_CHARACTERS||'characters')};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env}),report={loops:0,checks:0,maxDelta:0,samples:[],pause:[],errors:[]};
try{
 const pet=await app.firstWindow();await app.context().setOffline(true);pet.on('pageerror',e=>report.errors.push(String(e)));const panel=await openTestPanel(app,pet);
 await pet.waitForFunction(()=>window.petDiagnostics?.frames>5&&!window.petDiagnostics.loading);
 await app.evaluate(({screen})=>{screen.getCursorScreenPoint=()=>({x:-99999,y:-99999});});
 await panel.evaluate(()=>window.panel.command('furniture','f210327_0'));await pet.waitForFunction(()=>window.petDiagnostics?.sceneAction==='f210327_0'&&!window.petDiagnostics.loading);
 await pet.evaluate(()=>{window.petDiagnostics.measurePose=true;});
 await pet.waitForFunction(()=>Array.isArray(window.petDiagnostics.particleStates));
 let previous;const start=Date.now();
 while(Date.now()-start<21000){
  const d=await pet.evaluate(()=>({shaderTime:window.petDiagnostics.shaderTime,time:window.petDiagnostics.actionTime,states:window.petDiagnostics.particleStates?.filter(p=>p.source.includes('/water_base')),memory:window.petDiagnostics.memory}));
  assert.ok(d.states?.length,'background particle diagnostics missing');report.samples.push(d);
  if(previous&&d.time<previous.time-.1){report.loops++;
   const delta=d.shaderTime-previous.shaderTime;assert.ok(delta>=0&&delta<1,'shader time jumped at loop');report.maxDelta=Math.max(report.maxDelta,delta);report.checks++;await pet.screenshot({path:`test-results/water038-loop-${report.loops}.png`,omitBackground:true});
  }
  previous=d;await pet.waitForTimeout(70);
 }
 assert.ok(report.loops>=3&&report.checks>0);
 // Exercise the same suspend/resume notification as the main process.
 await app.evaluate(({powerMonitor})=>powerMonitor.emit('suspend'));await pet.waitForTimeout(150);const before=await pet.evaluate(()=>window.petDiagnostics.actionTime);await pet.waitForTimeout(700);const after=await pet.evaluate(()=>window.petDiagnostics.actionTime);assert.equal(after,before);report.pause=[before,after];
 await app.evaluate(({powerMonitor})=>powerMonitor.emit('resume'));await pet.waitForTimeout(250);assert.notEqual(await pet.evaluate(()=>window.petDiagnostics.actionTime),after);
 assert.deepEqual(report.errors,[]);report.complete=true;
}finally{writeFileSync('test-results/water038-runtime.json',JSON.stringify(report,null,2));await app.close();}
console.log(JSON.stringify({complete:report.complete,loops:report.loops,checks:report.checks,maxDelta:report.maxDelta}));
