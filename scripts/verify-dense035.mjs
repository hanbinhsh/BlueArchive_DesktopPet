import {openTestPanel} from './themed-menu-test-helper.mjs';
import {_electron as electron} from 'playwright';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const base=path.resolve('release/v0.2.14-final/win-unpacked'),profile=path.resolve('test-results/dense035-profile');
mkdirSync(profile,{recursive:true});mkdirSync('test-results/dense035',{recursive:true});
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'eimi_swimsuit',size:360,position:{x:40,y:40},eyeFollow:false,randomIdle:false,roaming:false}));
const env={...process.env,BA_TEST_DATA:profile,BA_CHARACTERS:path.join(base,'resources/characters')};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({executablePath:path.join(base,'BA Desktop Pet.exe'),args:[],env}),report={complete:false,errors:[],scenes:[],sequence:[]};
try{
 const pet=await app.firstWindow();await app.context().setOffline(true);pet.on('pageerror',e=>report.errors.push(String(e)));pet.on('console',m=>{if(m.type()==='error')report.errors.push(m.text());});
 const panel=await openTestPanel(app,pet);await app.evaluate(({screen})=>{screen.getCursorScreenPoint=()=>({x:-99999,y:-99999});});
 let selected='eimi_swimsuit';
 async function select(id){if(id!==selected){const loaded=pet.waitForEvent('load');await panel.evaluate(id=>window.panel.command('select',id),id);await loaded;selected=id;}await pet.waitForFunction(()=>window.petDiagnostics?.frames>5&&!window.petDiagnostics.loading);}
 for(const [character,id,rotate] of [['eimi_swimsuit','f210327_0',true],['kokona','f1100_0',false],['kikyou_swimsuit','f210372_0',true],['mine','f207310_0',false],['maki_camp','f210359_0',true]]){
  await select(character);const c=JSON.parse(readFileSync(path.join(env.BA_CHARACTERS,character,'character.json'),'utf8')),f=c.furniture.find(f=>f.id===id);
  await panel.evaluate(id=>window.panel.command('furniture',id),id);await pet.waitForFunction(id=>window.petDiagnostics?.sceneAction===id&&!window.petDiagnostics.loading,id);
  const samples=[];
  // Dense fixed-time sampling covers start/stop tracks; yaw also exercises transparent sorting.
  for(let i=0;i<=Math.floor(f.duration*4);i++){
   const time=i/4,yaw=rotate?Math.sin(time/f.duration*Math.PI*4)*.8:0;
   await panel.evaluate(yaw=>window.panel.command('settings',{yaw,pitch:0,roll:0}),yaw);
   await pet.evaluate(time=>{window.petDiagnostics.freezeTime=time;window.petDiagnostics.measurePose=true;window.petDiagnostics.measureFace=true;},time);await pet.waitForTimeout(85);
   const d=await pet.evaluate(()=>window.petDiagnostics);assert.equal(d.error,null);assert.equal(d.sceneAction,id);
   const file=`test-results/dense035/${character}-${String(i).padStart(3,'0')}.png`;await pet.screenshot({path:file,omitBackground:true});
   samples.push({time,yaw,file,actionTime:d.actionTime,face:d.face,pose:d.pose,particles:d.particleStates});
  }
  report.scenes.push({character,id,samples});console.log(character,samples.length);
  await pet.evaluate(()=>{delete window.petDiagnostics.freezeTime;});await panel.evaluate(()=>window.panel.command('stop-test'));
 }
 await select('hina_pajamas');await panel.evaluate(()=>window.panel.command('settings',{yaw:0,playbackSpeed:4,transitionSpeed:1}));
 let reloads=0;pet.on('load',()=>reloads++);
 await panel.evaluate(()=>window.panel.command('preview',{id:'sofa-check',name:'沙发连续片段',steps:['bedroom_windowsofa_start','bedroom_windowsofa_ing','bedroom_windowsofa_end'].map(id=>({kind:'furniture',id,mode:'count',value:1,gap:0}))}));
 const start=Date.now();let begun=false;
 while(Date.now()-start<25000){const state=await panel.evaluate(()=>window.panel.state());if(state.playback)begun=true;const d=await pet.evaluate(()=>window.petDiagnostics);report.sequence.push({ms:Date.now()-start,scene:d.sceneKey,action:d.sceneAction,loading:d.loading,loads:d.sceneLoads,error:d.error});assert.equal(d.error,null);if(begun&&!state.playback)break;await pet.waitForTimeout(100);}
 assert.ok(begun);assert.equal(reloads,0);const playing=report.sequence.filter(r=>r.scene!=='model.glb');assert.equal(new Set(playing.map(r=>r.scene)).size,1,'sofa clips must share one GLB');for(const id of ['bedroom_windowsofa_start','bedroom_windowsofa_ing','bedroom_windowsofa_end'])assert.ok(playing.some(s=>s.action===id),id);
 assert.equal((await panel.evaluate(()=>window.panel.state())).playback,undefined);assert.deepEqual(report.errors,[]);report.complete=true;
}finally{writeFileSync('test-results/dense035-runtime.json',JSON.stringify(report,null,2));await app.close();}
console.log('dense035 complete',report.complete);
