import {_electron as electron} from 'playwright';
import {openTestPanel} from './themed-menu-test-helper.mjs';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const exe=path.resolve('release/v0.2.19/win-unpacked/BA Desktop Pet.exe'),root=path.join(path.dirname(exe),'resources/characters');
const profile=path.resolve('test-results/ichika041-profile');mkdirSync(profile,{recursive:true});
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'ichika',size:420,allowOffscreen:true,eyeFollow:false,randomIdle:false,roaming:false,yaw:0,pitch:0,roll:0,position:{x:20,y:20}}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({executablePath:exe,args:[],env}),results=[],errors=[];
try{
 const pet=await app.firstWindow();await app.context().setOffline(true);pet.on('pageerror',e=>errors.push(String(e)));pet.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 const panel=await openTestPanel(app,pet);
 await app.evaluate(({BrowserWindow,screen})=>{const w=BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html'));w.setFocusable(false);w.setBounds({...w.getBounds(),x:-4000,y:100});screen.getCursorScreenPoint=()=>({x:-100000,y:-100000});});
 for(const character of ['ichika','ichika_swimsuit']){
  if(character!=='ichika'){const loaded=pet.waitForEvent('load');await panel.evaluate(id=>window.panel.command('select',id),character);await loaded;}
  await pet.waitForFunction(()=>window.petDiagnostics?.frames>5&&!window.petDiagnostics.loading);
  const c=JSON.parse(readFileSync(path.join(root,character,'character.json'),'utf8'));
  const actions=[];
  for(const id of ['idle','interact','pickup']){
   await pet.evaluate(()=>{delete window.petDiagnostics.freezeTime;window.petDiagnostics.measureFace=true;});
   await app.evaluate(({BrowserWindow},id)=>BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html')).webContents.send('pet:action',id),id);
   await pet.waitForFunction(id=>window.petDiagnostics.action===id&&!window.petDiagnostics.loading,id);await pet.waitForTimeout(220);
   const duration=await pet.evaluate(id=>window.petDiagnostics.durations[id],id),frames=[];
   for(let i=0;i<12;i++){
    const t=duration*i/12;await pet.evaluate(t=>window.petDiagnostics.freezeTime=t,t);await pet.waitForTimeout(90);
    const d=await pet.evaluate(()=>window.petDiagnostics);assert.equal(d.error,null);assert.equal(d.action,id);
    assert.ok(Object.values(d.face).flat().every(Number.isFinite));
    const file=`ichika041-${character}-${id}-${i}.png`;await pet.screenshot({path:'test-results/'+file,omitBackground:true});frames.push({time:t,file,face:d.face});
   }
   actions.push({id,duration,frames});
  }
  // Follow the real clock through the whole interaction, rather than relying
  // only on freeze-time screenshots. The original clip must move eye bones
  // and then restore its own idle normally.
  await pet.evaluate(()=>{delete window.petDiagnostics.freezeTime;});
  await panel.evaluate(()=>window.panel.command('settings',{eyeFollow:true}));
  await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html')).webContents.send('pet:action','interact'));
  await pet.waitForFunction(()=>window.petDiagnostics.action==='interact');
  const live=[];const duration=actions.find(a=>a.id==='interact').duration;const start=Date.now();
  while(Date.now()-start<(duration+.7)*1000){const d=await pet.evaluate(()=>window.petDiagnostics);assert.equal(d.error,null);live.push({time:d.actionTime,action:d.action,face:d.face,gaze:d.gaze});await pet.waitForTimeout(100);}
  assert.equal(live.at(-1).action,'idle');
  const baseline=live.find(d=>d.action==='interact')?.face;
  const changed=new Set();for(const d of live.filter(d=>d.action==='interact'))for(const [name,v]of Object.entries(d.face))if(/eye/i.test(name)&&v.some((x,i)=>Math.abs(x-(baseline[name]?.[i]??x))>1e-4))changed.add(name);
  assert.ok(changed.size>0);actions.push({id:'real-clock-with-eye-follow',changedEyeBones:[...changed],samples:live});
  await panel.evaluate(()=>window.panel.command('settings',{eyeFollow:false}));
  results.push({character,actions});console.log(character,'full eye cycle and return to idle passed');
 }
 assert.deepEqual(errors,[]);writeFileSync('test-results/ichika041-runtime.json',JSON.stringify({complete:true,executable:exe,results,errors},null,2));
}finally{await app.close();}
