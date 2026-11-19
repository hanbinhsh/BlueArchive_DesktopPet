import {openTestPanel} from './themed-menu-test-helper.mjs';
import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const tag=process.env.BA_SPEED_TAG||'qol-speeds',report={complete:false,cases:[],errors:[]};
for(const character of ['kisaki','hina_pajamas']){
 const profile=path.resolve(`test-results/${tag}-${character}`);mkdirSync(profile,{recursive:true});writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character,size:360,position:{x:20,y:20}}));
 const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
 const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env});
 const child=app.process();
 try{
  const pet=await app.firstWindow();await pet.waitForFunction(()=>window.petDiagnostics?.frames>5);pet.on('pageerror',e=>report.errors.push(e.message));await app.context().setOffline(true);
 await app.evaluate(({screen})=>{screen.getCursorScreenPoint=()=>({x:-10000,y:-10000});});const panel=await openTestPanel(app,pet);panel.on('pageerror',e=>report.errors.push(e.message));
  const command=(name,value)=>panel.evaluate(({name,value})=>window.panel.command(name,value).then(()=>{}),{name,value});
  const testedAction=await pet.evaluate(()=>window.petDiagnostics.durations.pickup?'pickup':'interact');await pet.evaluate(()=>{window.petDiagnostics.measurePose=true;window.petDiagnostics.measureFace=true;});
  for(const [playbackSpeed,transitionSpeed]of [[.25,.25],[4,.25],[.25,4],[4,4]]){
   await command('stop-test');await pet.waitForTimeout(850);await command('settings',{playbackSpeed,transitionSpeed,pitch:Math.PI*2+Math.PI/6,yaw:Math.PI*2+Math.PI/6,roll:Math.PI*2+Math.PI/6});await command('preview',{id:'speed',name:'倍速验证',steps:[{kind:'action',id:testedAction,mode:'seconds',value:1.4,gap:.4}]});
   const samples=[],begin=Date.now();let gapTime;
   while(Date.now()-begin<4000){const s=await panel.evaluate(async()=>{const v=await window.panel.state();return v.playback;});const d=await pet.evaluate(()=>window.petDiagnostics);assert.equal(d.error,null);if(d.pose){assert.ok(d.pose.size.every(Number.isFinite));assert.ok(Math.max(...d.pose.size)<8,'prop scale spike');assert.ok(d.pose.halo.every(Number.isFinite));}
    samples.push({ms:Date.now()-begin,phase:s?.phase,time:d.actionTime,action:d.action,transition:d.transition,mouth:d.mouthTile,halo:d.pose?.halo,face:d.face});
    if(s?.phase==='gap'&&d.action===testedAction&&d.playbackToken===s.token){if(gapTime===undefined)gapTime=d.actionTime;else assert.equal(d.actionTime,gapTime,'gap must hold last frame');}
    if(!s)break;await pet.waitForTimeout(20);
   }
   assert.ok(samples.at(-1).ms>=1700,'real seconds and gap independent of speed');assert.ok(samples.some(s=>s.phase==='gap'));
   const blending=samples.filter(s=>s.action===testedAction&&s.transition.remaining>0);if(transitionSpeed<4)assert.ok(blending.length>0);const measured=blending.length?blending.at(-1).ms-blending[0].ms:0;report.cases.push({character,playbackSpeed,transitionSpeed,measuredBlendMs:measured,elapsedMs:samples.at(-1).ms,samples});assert.ok(Math.abs(measured-.18/transitionSpeed*1000)<180,`transition must use its own clock: measured ${measured} ms`);
   await pet.waitForTimeout(850);await pet.screenshot({path:`test-results/${tag}-${character}-${playbackSpeed}-${transitionSpeed}.png`,omitBackground:true});
  }
  const f=(await pet.evaluate(()=>window.pet.init())).character.furniture[0];await command('settings',{playbackSpeed:4,transitionSpeed:.25});await command('preview',{id:'furniture',name:'家具倍速',steps:[{kind:'furniture',id:f.id,mode:'seconds',value:1,gap:.3},{kind:'action',id:'interact',mode:'count',value:2,gap:.2}]});
  await pet.waitForFunction(()=>window.petDiagnostics.sceneKey!=='model.glb'&&!window.petDiagnostics.loading);await pet.screenshot({path:`test-results/${tag}-${character}-furniture.png`,omitBackground:true});
  await panel.waitForFunction(async()=>!(await window.panel.state()).playback,null,{timeout:60000});assert.equal(await pet.evaluate(()=>window.petDiagnostics.error),null);
 }finally{await app.evaluate(({app})=>app.exit(0)).catch(()=>{});child.kill();writeFileSync(`test-results/${tag}.json`,JSON.stringify(report,null,2));}
}
assert.deepEqual(report.errors,[]);report.complete=true;writeFileSync(`test-results/${tag}.json`,JSON.stringify(report,null,2));console.log('Playback / transition independence, real seconds, held gaps, prop size and mixed-scene loops passed');

process.exit(0);
