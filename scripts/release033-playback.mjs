import {_electron as electron} from 'playwright';
import {openTestPanel} from './themed-menu-test-helper.mjs';
import {mkdirSync,writeFileSync,readFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const profile=path.resolve('test-results/release033-playback-profile');mkdirSync(profile,{recursive:true});
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'chinatsu_onsen',size:280,randomIdle:false,roaming:false,eyeFollow:false}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;delete env.BA_CHARACTERS;
const app=await electron.launch({executablePath:path.resolve('release/v0.2.13/win-unpacked/BA Desktop Pet.exe'),args:[],env});
const report={complete:false,version:await app.evaluate(({app})=>app.getVersion()),errors:[],cases:[]};
try {
 const pet=await app.firstWindow();pet.on('pageerror',e=>report.errors.push(e.message));pet.on('console',m=>{if(m.type()==='error')report.errors.push(m.text());});
 await app.context().setOffline(true);
 await pet.waitForFunction(()=>window.petDiagnostics?.frames>5&&!window.petDiagnostics.loading);
 await app.evaluate(({screen})=>{screen.getCursorScreenPoint=()=>({x:-10000,y:-10000});});
 const panel=await openTestPanel(app,pet);let selected='chinatsu_onsen';
 for(const item of [{character:'chinatsu_onsen',id:'f6200_0',time:40},{character:'izuna',id:'f203303_0',time:9.4},{character:'mari',id:'f207314_1',time:16.5}]) {
  if(selected!==item.character){const loaded=pet.waitForEvent('load');await panel.evaluate(id=>window.panel.command('select',id),item.character);await loaded;await pet.waitForFunction(()=>window.petDiagnostics?.frames>5&&!window.petDiagnostics.loading);selected=item.character;}
  await panel.evaluate(id=>window.panel.command('furniture',id),item.id);
  await pet.waitForFunction(id=>window.petDiagnostics.sceneAction===id&&!window.petDiagnostics.loading,item.id);
  let reference;
  for(const rate of [1,.25,4]) {
   await panel.evaluate(playbackSpeed=>window.panel.command('settings',{playbackSpeed}),rate);await pet.waitForTimeout(120);
   await pet.evaluate(time=>{window.petDiagnostics.measurePose=true;window.petDiagnostics.freezeTime=time;},item.time/rate);await pet.waitForTimeout(200);
   const state=await pet.evaluate(()=>({time:window.petDiagnostics.actionTime,particles:window.petDiagnostics.particleStates.filter(p=>p.visible).map(p=>({name:p.name,opacity:p.opacity,scale:p.scale,position:p.position}))}));
   assert.ok(Math.abs(state.time-item.time)<1e-6);assert.ok(state.particles.length>0);
   if(reference)assert.deepEqual(state,reference);else reference=state;
  }
  await pet.evaluate(()=>{delete window.petDiagnostics.freezeTime;});
  await panel.evaluate(()=>window.panel.command('settings',{playbackSpeed:1}));
  const entry={id:'verify033',name:'家具完整播放回归',steps:[{kind:'furniture',id:item.id,mode:'count',value:1,gap:0},{kind:'action',id:'interact',mode:'count',value:1,gap:0}]};
  await panel.evaluate(entry=>window.panel.command('preview',entry),entry);
  await panel.waitForFunction(async()=>Boolean((await window.panel.state()).playback));
  const started=Date.now();let reloads=0;const onLoad=()=>reloads++;pet.on('load',onLoad);
  const manifest=JSON.parse(readFileSync(`characters/${item.character}/character.json`));
  const duration=manifest.furniture.find(f=>f.id===item.id).duration;
  while((await panel.evaluate(()=>window.panel.state())).playback){assert.ok(Date.now()-started<(duration+45)*1000,'sequence did not finish');await pet.waitForTimeout(250);}
  await pet.waitForFunction(()=>!window.petDiagnostics.loading&&window.petDiagnostics.sceneKey==='model.glb');
  pet.off('load',onLoad);assert.equal(reloads,0);
  assert.equal(await pet.evaluate(()=>window.petDiagnostics.error),null);
  report.cases.push({...item,rates:[.25,1,4],matchingVisibleParticles:reference.particles.length,completedSequenceSeconds:(Date.now()-started)/1000,returnedToCharacter:true,reloads});
 }
 assert.deepEqual(report.errors,[]);report.complete=true;
} finally {writeFileSync('test-results/release033-playback.json',JSON.stringify(report,null,2));await app.close();}
console.log(JSON.stringify(report,null,2));
