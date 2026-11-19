import {openTestPanel} from './themed-menu-test-helper.mjs';
import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync,appendFileSync,readFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const tag=process.env.BA_SOAK_TAG||'release043-soak',minutes=Number(process.env.BA_SOAK_MINUTES||30),profile=path.resolve(`test-results/${tag}-profile`);
mkdirSync(profile,{recursive:true});writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'eri',size:280,allowOffscreen:true,position:{x:-4000,y:20},outline:true,outlineWidth:38,playbackSpeed:1,transitionSpeed:1,randomIdle:false,roaming:false}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({...(process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']}),env});
await app.firstWindow();
const report={complete:false,version:await app.evaluate(({app})=>app.getVersion()),minutes,cycles:0,selections:0,reloads:0,errors:[],samples:[]};
writeFileSync(`test-results/${tag}.jsonl`,'');const child=app.process();
try{
 const pet=await app.firstWindow();pet.on('pageerror',e=>report.errors.push(e.message));pet.on('console',m=>{if(m.type()==='error')report.errors.push(m.text());});
 await pet.waitForFunction(()=>window.petDiagnostics?.frames>5&&!window.petDiagnostics.loading,null,{timeout:60000});await app.context().setOffline(true);
 await app.evaluate(({screen,BrowserWindow})=>{screen.getCursorScreenPoint=()=>({x:-10000,y:-10000});const w=BrowserWindow.getAllWindows()[0];w.setFocusable(false);w.setBounds({...w.getBounds(),x:-4000,y:100});});
 const panel=await openTestPanel(app,pet);await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('panel.html')).hide());
 pet.on('load',()=>report.reloads++);
 const f=(id,seconds)=>({kind:'furniture',id,mode:'seconds',value:seconds,gap:0});
 const cases=[{character:'ui',steps:[f('f204301_0',34)]},{character:'subaru',steps:[f('f210384_0',38)]},{character:'hasumi_track',steps:[f('f10300_0',28)]},{character:'hanako_swimsuit',steps:[f('f210316_0',28)]},{character:'mine',steps:[f('f207310_0',28)]},{character:'azusa_racing',steps:[f('fevent097_racinggame_0',30)]},{character:'hina_swimsuit',steps:[f('f4301_0',28)]},{character:'mika',steps:[f('f207312_1',28)]}];
 if(process.env.BA_SOAK_CASES)cases.splice(0,cases.length,...JSON.parse(readFileSync(process.env.BA_SOAK_CASES,'utf8')));
 const started=Date.now();let selected='eri',caseIndex=0,nextSample=0,lastFrameSample,frameCount=0,frameSeconds=0;
 while(Date.now()-started<minutes*60000){
  const item=cases[caseIndex++%cases.length];
  if(selected!==item.character){report.selections++;const loaded=pet.waitForEvent('load');await panel.evaluate(id=>window.panel.command('select',id),item.character);await loaded;await pet.waitForFunction(()=>window.petDiagnostics?.frames>5&&!window.petDiagnostics.loading,null,{timeout:60000});selected=item.character;lastFrameSample=undefined;}
  const entry={id:'soak',name:'贴图与粒子稳定性测试',steps:[...item.steps,{kind:'action',id:'interact',mode:'count',value:1,gap:0}]};
  await panel.evaluate(e=>window.panel.command('preview',e),entry);const cycleStart=Date.now();
  while(true){
   const state=await panel.evaluate(async()=>{const s=await window.panel.state();return {playback:s.playback,error:s.error};});assert.equal(state.error,undefined);if(!state.playback)break;
   assert.ok(Date.now()-cycleStart<180000,'sequence stuck');
   if(Date.now()>=nextSample){
    nextSample=Date.now()+10000;const d=await pet.evaluate(()=>({frames:window.petDiagnostics.frames,error:window.petDiagnostics.error,memory:window.petDiagnostics.memory,cached:window.petDiagnostics.cachedScenes,loads:window.petDiagnostics.sceneLoads,scene:window.petDiagnostics.sceneKey,heap:performance.memory?.usedJSHeapSize}));assert.equal(d.error,null);assert.ok(d.cached<=3);
    const metrics=await app.evaluate(({app})=>app.getAppMetrics().map(p=>({type:p.type,cpu:p.cpu.percentCPUUsage,memoryMiB:p.memory.workingSetSize/1024})));
    const sample={seconds:(Date.now()-started)/1000,character:selected,cycle:report.cycles,diagnostics:d,metrics};report.samples.push(sample);appendFileSync(`test-results/${tag}.jsonl`,JSON.stringify(sample)+'\n');
    if(lastFrameSample){frameCount+=d.frames-lastFrameSample.frames;frameSeconds+=sample.seconds-lastFrameSample.seconds;}lastFrameSample={frames:d.frames,seconds:sample.seconds};
    if(report.samples.length%6===0)console.log(`${Math.round(sample.seconds/60)} min, cycles=${report.cycles}, character=${selected}, memory=${Math.round(metrics.reduce((n,p)=>n+p.memoryMiB,0))} MiB, resources=${JSON.stringify(d.memory)}`);
   }
   // Finish the last combination so cycles only counts complete playbacks.
   await pet.waitForTimeout(200);
  }
  report.cycles++;
 }
 await panel.evaluate(()=>window.panel.command('stop-test'));await pet.waitForTimeout(1000);
 const stable=report.samples.filter(s=>s.seconds>=120),total=s=>s.metrics.reduce((n,p)=>n+p.memoryMiB,0),mean=a=>a.reduce((n,s)=>n+total(s),0)/a.length;
 report.elapsedSeconds=(Date.now()-started)/1000;report.fps=frameCount/frameSeconds;
 report.memoryMiB={min:Math.min(...stable.map(total)),max:Math.max(...stable.map(total)),previousFiveMinutes:mean(stable.filter(s=>s.seconds>=minutes*60-600&&s.seconds<minutes*60-300)),lastFiveMinutes:mean(stable.filter(s=>s.seconds>=minutes*60-300))};
 assert.equal(report.reloads,report.selections);assert.deepEqual(report.errors,[]);assert.ok(report.fps>=20,'rendering too slow');
 assert.ok(report.memoryMiB.lastFiveMinutes<=report.memoryMiB.previousFiveMinutes*1.15+30,'working set still growing late in soak');report.complete=true;
}finally{writeFileSync(`test-results/${tag}.json`,JSON.stringify(report,null,2));await app.evaluate(({app})=>app.exit(0)).catch(()=>{});child.kill();}
console.log(JSON.stringify({complete:report.complete,version:report.version,cycles:report.cycles,seconds:report.elapsedSeconds,fps:report.fps,memoryMiB:report.memoryMiB}));
process.exit(0);
