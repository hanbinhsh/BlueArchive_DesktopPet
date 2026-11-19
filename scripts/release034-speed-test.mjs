import {_electron as electron} from 'playwright';
import {openTestPanel} from './themed-menu-test-helper.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const profile=path.resolve('test-results/release034-speed-profile');mkdirSync(profile,{recursive:true});
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'aris_battle',size:280,eyeFollow:false,randomIdle:false,roaming:false}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;delete env.BA_CHARACTERS;
const executable=path.resolve('release/v0.2.14/win-unpacked/BA Desktop Pet.exe');
const app=await electron.launch({executablePath:executable,args:[],env}),report={executable,errors:[],cases:[]};
try{
 const pet=await app.firstWindow();pet.on('pageerror',e=>report.errors.push(e.message));pet.on('console',m=>{if(m.type()==='error')report.errors.push(m.text());});
 await app.context().setOffline(true);await pet.waitForFunction(()=>window.petDiagnostics?.frames>5&&!window.petDiagnostics.loading);
 await app.evaluate(({screen})=>{screen.getCursorScreenPoint=()=>({x:-10000,y:-10000});});
 const panel=await openTestPanel(app,pet);let selected='aris_battle';
 const cases=[{character:'ui',furniture:'f204301_0',time:9.4},{character:'ui',furniture:'f204301_0',time:10.3},{character:'subaru',furniture:'f210384_0',time:10},{character:'hina_swimsuit',furniture:'f4301_0',time:6},{character:'aris_battle',furniture:'f210394_0',time:18.26},{character:'mine',furniture:'f207310_0',time:16.8},{character:'hifumi_racing',furniture:'fevent097_racinggame_0',time:28},{character:'kikyou_swimsuit',furniture:'f210372_0',time:19.8},{character:'hanako_swimsuit',furniture:'f210316_0',time:4.6},{character:'tsumugi',furniture:'f211318_0',time:20}];
 const compare=(a,b,label)=>{if(typeof a==='number'){assert.ok(Math.abs(a-b)<1e-6,`${label}: ${a} / ${b}`);return;}if(Array.isArray(a)){assert.equal(a.length,b.length,label);for(let i=0;i<a.length;i++)compare(a[i],b[i],`${label}[${i}]`);return;}if(a&&typeof a==='object'){assert.deepEqual(Object.keys(a),Object.keys(b),label);for(const k of Object.keys(a))compare(a[k],b[k],`${label}.${k}`);return;}assert.equal(a,b,label);};
 for(const item of cases){
  await pet.evaluate(()=>{delete window.petDiagnostics.freezeTime;});
  if(selected!==item.character){const loaded=pet.waitForEvent('load');await panel.evaluate(id=>window.panel.command('select',id),item.character);await loaded;await pet.waitForFunction(()=>window.petDiagnostics?.frames>5&&!window.petDiagnostics.loading);selected=item.character;}
  await panel.evaluate(id=>window.panel.command('furniture',id),item.furniture);await pet.waitForFunction(id=>window.petDiagnostics.sceneAction===id&&!window.petDiagnostics.loading,item.furniture);await pet.waitForTimeout(400);
  let reference;
  for(const rate of [1,.25,4]){
   await panel.evaluate(playbackSpeed=>window.panel.command('settings',{playbackSpeed}),rate);await pet.waitForTimeout(120);
   await pet.evaluate(time=>{window.petDiagnostics.measurePose=true;window.petDiagnostics.measureFace=true;window.petDiagnostics.freezeTime=time;},item.time/rate);await pet.waitForTimeout(200);
   const state=await pet.evaluate(()=>{const d=window.petDiagnostics;return {time:d.actionTime,mouth:d.mouthMaps,face:d.face,particles:d.particleStates.filter(p=>p.visible).map(p=>({name:p.name,opacity:p.opacity,scale:p.scale,position:p.position}))};});
   assert.ok(Math.abs(state.time-item.time)<1e-6);if(reference)compare(state,reference,`${item.character} ${rate}x`);else reference=state;
  }
  report.cases.push({...item,rates:[1,.25,4],matchingParticles:reference.particles.length,matchingFaceTracks:Object.keys(reference.face).length});
 }
 await pet.evaluate(()=>{delete window.petDiagnostics.freezeTime;});await pet.waitForTimeout(200);
 await app.evaluate(({powerMonitor})=>powerMonitor.emit('suspend'));await pet.waitForTimeout(100);const paused=await pet.evaluate(()=>({frames:window.petDiagnostics.frames,time:window.petDiagnostics.actionTime}));await pet.waitForTimeout(1000);assert.deepEqual(await pet.evaluate(()=>({frames:window.petDiagnostics.frames,time:window.petDiagnostics.actionTime})),paused);
 await app.evaluate(({powerMonitor})=>powerMonitor.emit('resume'));await pet.waitForFunction(frames=>window.petDiagnostics.frames>frames,paused.frames);report.simulatedSuspendPause=true;
 assert.deepEqual(report.errors,[]);
}finally{writeFileSync('test-results/release034-speed.json',JSON.stringify(report,null,2));await app.close();}
console.log(JSON.stringify(report,null,2));
