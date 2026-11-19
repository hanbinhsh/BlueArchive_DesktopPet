import {openTestPanel} from './themed-menu-test-helper.mjs';
import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync,appendFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const tag=process.env.BA_SOAK_TAG||'release027-soak',minutes=Number(process.env.BA_SOAK_MINUTES||30),profile=path.resolve(`test-results/${tag}-profile`);
const particleSoak=process.env.BA_SOAK_PARTICLES==='1';
mkdirSync(profile,{recursive:true});writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:particleSoak?'rio_battle':'hina_pajamas',size:280,position:{x:20,y:20},outline:true,outlineWidth:38,playbackSpeed:2,transitionSpeed:1,randomIdle:false,roaming:false}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env});
const report={complete:false,executable:process.env.BA_EXECUTABLE||'development',minutes,cycles:0,reloads:0,errors:[],samples:[]};
writeFileSync(`test-results/${tag}.jsonl`,'');
const child=app.process();
try{
 const pet=await app.firstWindow();pet.on('pageerror',e=>report.errors.push(e.message));pet.on('console',m=>{if(m.type()==='error')report.errors.push(m.text());});
 await pet.waitForFunction(()=>window.petDiagnostics?.frames>5,null,{timeout:60000});await app.context().setOffline(true);
 await app.evaluate(({screen,BrowserWindow})=>{screen.getCursorScreenPoint=()=>({x:-10000,y:-10000});BrowserWindow.getAllWindows()[0].setFocusable(false);});
 const panel=await openTestPanel(app,pet);
 await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('panel.html')).hide());
 pet.on('load',()=>report.reloads++);
 const entry={id:'soak',name:'家具切换稳定性测试',steps:[
  {kind:'action',id:'interact',mode:'count',value:1,gap:.1},
  {kind:'furniture',id:'bedroom_windowsofa_start',mode:'count',value:1,gap:0},
  {kind:'furniture',id:'bedroom_windowsofa_ing',mode:'seconds',value:2,gap:.2},
  {kind:'furniture',id:'bedroom_windowsofa_end',mode:'count',value:1,gap:0},
  {kind:'furniture',id:'bedroom_bed_day01_ing',mode:'seconds',value:2,gap:0},
  {kind:'furniture',id:'bedroom_bed_day00_ing',mode:'seconds',value:2,gap:.2},
  {kind:'action',id:'idle',mode:'seconds',value:1,gap:0}
 ]};
 if(particleSoak)entry.steps=[{kind:'furniture',id:'f210391_0',mode:'seconds',value:20,gap:0},{kind:'furniture',id:'f210391_1',mode:'seconds',value:20,gap:0},{kind:'action',id:'interact',mode:'count',value:1,gap:0}];
 const started=Date.now();let lastSample=0,cycleStarted=0,cycleActive=false;
 while(Date.now()-started<minutes*60000){
  const current=await panel.evaluate(async()=>{const s=await window.panel.state();return {playback:s.playback,error:s.error};});assert.equal(current.error,undefined);
  if(!current.playback){if(cycleActive)report.cycles++;await panel.evaluate(e=>window.panel.command('preview',e).then(()=>{}),entry);cycleStarted=Date.now();cycleActive=true;}
  assert.ok(Date.now()-cycleStarted<90000,'sequence stuck');
  if(Date.now()-lastSample>=10000){
   lastSample=Date.now();const d=await pet.evaluate(()=>({frames:window.petDiagnostics.frames,error:window.petDiagnostics.error,memory:window.petDiagnostics.memory,cached:window.petDiagnostics.cachedScenes,loads:window.petDiagnostics.sceneLoads,scene:window.petDiagnostics.sceneKey,heap:performance.memory?.usedJSHeapSize}));assert.equal(d.error,null);assert.ok(d.cached<=3);
   const metrics=await app.evaluate(({app})=>app.getAppMetrics().map(p=>({type:p.type,pid:p.pid,cpu:p.cpu.percentCPUUsage,memoryMiB:p.memory.workingSetSize/1024})));
   const sample={seconds:(Date.now()-started)/1000,cycles:report.cycles,playback:current.playback,diagnostics:d,metrics};report.samples.push(sample);appendFileSync(`test-results/${tag}.jsonl`,JSON.stringify(sample)+'\n');
   if(report.samples.length%6===0)console.log(`${Math.round(sample.seconds/60)} min, cycles=${report.cycles}, frames=${d.frames}, total=${Math.round(metrics.reduce((n,p)=>n+p.memoryMiB,0))} MiB, GPU resources=${JSON.stringify(d.memory)}`);
  }
  await pet.waitForTimeout(150);
 }
 await panel.evaluate(()=>window.panel.command('stop-test').then(()=>{}));await pet.waitForTimeout(1000);
 const stable=report.samples.filter(s=>s.seconds>=120),first=stable[0]||report.samples[0],last=report.samples.at(-1),total=s=>s.metrics.reduce((n,p)=>n+p.memoryMiB,0),mean=ss=>ss.reduce((n,s)=>n+total(s),0)/ss.length;
 report.elapsedSeconds=(Date.now()-started)/1000;report.fps=(last.diagnostics.frames-first.diagnostics.frames)/(last.seconds-first.seconds);
 report.memoryMiB={warm:total(first),final:total(last),min:Math.min(...stable.map(total)),max:Math.max(...stable.map(total)),previousFiveMinutes:mean(stable.filter(s=>s.seconds>=minutes*60-600&&s.seconds<minutes*60-300)),lastFiveMinutes:mean(stable.filter(s=>s.seconds>=minutes*60-300))};
 assert.equal(report.reloads,0);assert.deepEqual(report.errors,[]);assert.ok(report.fps>=20,'sustained rendering too slow');assert.ok(report.memoryMiB.lastFiveMinutes<=report.memoryMiB.previousFiveMinutes*1.15+30,'working set still growing late in soak');report.complete=true;
}finally{writeFileSync(`test-results/${tag}.json`,JSON.stringify(report,null,2));await app.evaluate(({app})=>app.exit(0)).catch(()=>{});child.kill();}
console.log(JSON.stringify({complete:report.complete,cycles:report.cycles,elapsedSeconds:report.elapsedSeconds,fps:report.fps,memoryMiB:report.memoryMiB}));

process.exit(0);
