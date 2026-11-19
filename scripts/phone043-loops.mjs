import {_electron as electron} from 'playwright';
import {openTestPanel} from './themed-menu-test-helper.mjs';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import path from 'node:path';import assert from 'node:assert/strict';
const executablePath=path.resolve('release/v0.2.21/win-unpacked/BA Desktop Pet.exe'),profile=path.resolve('test-results/phone043-loops-profile');mkdirSync(profile,{recursive:true});
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'ichika',size:360,allowOffscreen:true,eyeFollow:false,randomIdle:false,roaming:false,position:{x:20,y:20}}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;const app=await electron.launch({executablePath,args:[],env}),errors=[],samples=[],cycles=[];
const file='test-results/phone043-loops.json';
try{
 const pet=await app.firstWindow();await app.context().setOffline(true);pet.on('pageerror',e=>errors.push(String(e)));pet.on('console',e=>{if(e.type()==='error')errors.push(e.text());});
 const panel=await openTestPanel(app,pet);await app.evaluate(({BrowserWindow,screen})=>{const w=BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html'));w.setFocusable(false);w.setBounds({...w.getBounds(),x:-4000,y:100});screen.getCursorScreenPoint=()=>({x:-100000,y:-100000});});
 for(const [index,speed]of [1,1,2,.5].entries()){
  await panel.evaluate(playbackSpeed=>window.panel.command('settings',{playbackSpeed,transitionSpeed:1}),speed);
  const entry={id:'phone-loop-'+index,name:'手机屏幕完整循环',steps:[{kind:'furniture',id:'f10206_0',mode:'count',value:1,gap:0},{kind:'action',id:'interact',mode:'count',value:1,gap:0}]};
  await panel.evaluate(entry=>window.panel.command('preview',entry),entry);
  const start=Date.now();let seen=false,frames=0;
  while(true){
   const state=await panel.evaluate(()=>window.panel.state());const d=await pet.evaluate(()=>window.petDiagnostics);assert.equal(d.error,null);assert.ok(d.cachedScenes<=3);
   seen||=d.sceneAction==='f10206_0';
   samples.push({cycle:index,speed,elapsed:(Date.now()-start)/1000,scene:d.sceneAction,time:d.actionTime,frames:d.frames,memory:d.memory,cached:d.cachedScenes});
   if(!state.playback&&seen)break;assert.ok(Date.now()-start<65000);await pet.waitForTimeout(200);
  }
  assert.ok(seen);assert.equal(await pet.evaluate(()=>window.petDiagnostics.sceneKey),'model.glb');cycles.push({speed,seconds:(Date.now()-start)/1000});console.log('Phone scene and return',speed,'passed');
 }
 assert.deepEqual(errors,[]);writeFileSync(file,JSON.stringify({complete:true,executable:executablePath,version:await app.evaluate(({app})=>app.getVersion()),cycles,samples,errors},null,2));
}finally{await app.close();}
