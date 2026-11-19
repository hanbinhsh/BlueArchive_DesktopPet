import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync,readFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
const reportPath='test-results/hold043.json';
const results=process.env.BA_RESUME?JSON.parse(readFileSync(reportPath,'utf8')):[];
for(const character of process.argv.slice(2).length ? process.argv.slice(2) : ['serika','serika_newyear','serika_swimsuit','junko','junko_newyear','plana']) {
 const profile=path.resolve('test-results/hold043-profile');mkdirSync(profile,{recursive:true});
 writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character,allowOffscreen:true,size:360,yaw:0,pitch:0,position:{x:400,y:180}}));
 const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
 const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:process.env.BA_EXECUTABLE,args:[]}:{args:['.']},env});
 try {
  const page=await app.firstWindow();await page.waitForFunction(()=>window.petDiagnostics?.frames>5);
  await app.evaluate(({BrowserWindow})=>{const w=BrowserWindow.getAllWindows()[0];w.setFocusable(false);w.setBounds({...w.getBounds(),x:-4000,y:180});});
  const hasPickup=(await page.evaluate(()=>window.pet.init())).character.actions.some(a=>a.id==='pickup');
  await page.evaluate(()=>window.petDiagnostics.measurePose=true);
  await page.evaluate(()=>{
   window.holdInputEvents=[];
   for(const type of ['pointerdown','pointerup','pointercancel','lostpointercapture','blur','focus'])window.addEventListener(type,e=>window.holdInputEvents.push({type,time:performance.now(),action:window.petDiagnostics.action}),true);
  });
  // CDP pointer events do not move the Windows cursor. Mirror them into the
  // main-process cursor poll so the real cursor cannot erase synthetic hits.
  if(!process.env.BA_NATIVE)await app.evaluate(({screen})=>{
   globalThis.holdCursor={x:-100000,y:-100000};screen.getCursorScreenPoint=()=>globalThis.holdCursor;
  });
  async function moveMouse(x,y,options){
   if(!process.env.BA_NATIVE)await app.evaluate(({BrowserWindow},p)=>{
    const b=BrowserWindow.getAllWindows()[0].getBounds();globalThis.holdCursor={x:b.x+p.x,y:b.y+p.y};
   },{x,y});
   await page.mouse.move(x,y,options);
  }
  let point;
  for(let y=140;y<=330&&!point;y+=20)for(let x=180;x<=360&&!point;x+=30){await moveMouse(x,y);await page.waitForTimeout(40);if(await page.evaluate(()=>window.petDiagnostics.hit))point={x,y};}
  assert.ok(point);
  let native;
  if(process.env.BA_NATIVE) {
   const origin=await app.evaluate(({BrowserWindow,screen},p)=>{const b=BrowserWindow.getAllWindows()[0].getBounds();return screen.dipToScreenPoint({x:b.x+p.x,y:b.y+p.y});},point);
   const actions=[{type:'move',...origin},{type:'wait',ms:500},{type:'down'},{type:'wait',ms:100}];
   for(let i=0;i<80;i++)actions.push({type:'move',x:origin.x+20+Math.round(Math.sin(i/5)*100),y:origin.y+20+Math.round(Math.cos(i/5)*60)},{type:'wait',ms:200});
   actions.push({type:'wait',ms:9000},{type:'up'});
   const file=path.resolve('test-results/hold043-native-actions.json');writeFileSync(file,JSON.stringify(actions));
   native=promisify(execFile)('powershell.exe',['-NoProfile','-ExecutionPolicy','Bypass','-File',path.resolve('scripts/native-input.ps1'),'-ActionsFile',file],{windowsHide:true});
   await page.waitForFunction(id=>window.petDiagnostics.action===id,hasPickup?'pickup':'idle');
  }else{await page.mouse.down();await moveMouse(point.x+12,point.y+12,{steps:3});}
  const samples=[];
  for(let i=0;i<23;i++) {
   await page.waitForTimeout(1000);
   samples.push({diagnostics:await page.evaluate(()=>window.petDiagnostics),bounds:await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows()[0].getBounds())});
   if([1,16,22].includes(i))await page.screenshot({path:`test-results/hold043-${character}-${i}.png`,omitBackground:true});
  }
  writeFileSync(`test-results/hold043-${character}-trace.json`,JSON.stringify({samples,inputEvents:await page.evaluate(()=>window.holdInputEvents)},null,2));
  if(native)await native;else await page.mouse.up();await page.waitForFunction(()=>window.petDiagnostics.action==='idle');
  assert.equal(samples.at(-1).diagnostics.error,null);
  if(hasPickup) {
   assert.ok(samples.every(s=>s.diagnostics.action==='pickup'),'Drag must remain in pickup');
   assert.ok(samples.slice(1).some((s,i)=>s.diagnostics.actionTime<samples[i].diagnostics.actionTime),'Original pickup must loop rather than clamp');
  } else {
   assert.ok(samples.every(s=>s.diagnostics.action==='idle'),'Outfits without pickup must keep their own idle while dragged');
   assert.ok(samples.at(-1).diagnostics.frames>samples[0].diagnostics.frames+200,'Idle must continue rendering while dragged');
  }
  console.log(character,'window range',Math.min(...samples.map(s=>s.bounds.width)),Math.max(...samples.map(s=>s.bounds.width)),Math.min(...samples.map(s=>s.bounds.height)),Math.max(...samples.map(s=>s.bounds.height)));
  for(const sample of samples) {
   assert.ok(Math.abs(sample.bounds.width-540)<=3,`Window width grew: ${sample.bounds.width}`);
   assert.ok(Math.abs(sample.bounds.height-522)<=3,`Window height grew: ${sample.bounds.height}`);
   assert.ok(sample.diagnostics.pose.size.every(Number.isFinite));
  }
  results.push({character,samples});console.log(character,'held',samples.length,'samples; final:',samples.at(-1).diagnostics.pose);
 }finally{await app.close();}
 writeFileSync(reportPath,JSON.stringify(results,null,2));
}
