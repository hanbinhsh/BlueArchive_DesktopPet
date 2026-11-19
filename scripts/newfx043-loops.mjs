import {_electron as electron} from 'playwright';
import {openTestPanel} from './themed-menu-test-helper.mjs';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
const executablePath=path.resolve('release/v0.2.21/win-unpacked/BA Desktop Pet.exe'),profile=path.resolve('test-results/newfx043-profile');mkdirSync(profile,{recursive:true});
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'kanoe',size:280,allowOffscreen:true,eyeFollow:false,randomIdle:false,roaming:false,position:{x:-4000,y:100}}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;const app=await electron.launch({executablePath,args:[],env}),errors=[],cycles=[];
try{
 const pet=await app.firstWindow();await app.context().setOffline(true);pet.on('pageerror',e=>errors.push(String(e)));pet.on('console',e=>{if(e.type()==='error')errors.push(e.text());});
 const panel=await openTestPanel(app,pet);await app.evaluate(({BrowserWindow,screen})=>{const w=BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html'));w.setFocusable(false);w.setBounds({...w.getBounds(),x:-4000,y:100});screen.getCursorScreenPoint=()=>({x:-100000,y:-100000});});
 let selected='kanoe';
 for(const item of [{character:'kanoe',id:'f210379_0',speed:2},{character:'hare_camp',id:'f210329_0',speed:.5},{character:'atsuko_swimsuit',id:'f13204_0',speed:2}]){
  if(item.character!==selected){const loaded=pet.waitForEvent('load');await panel.evaluate(id=>window.panel.command('select',id),item.character);await loaded;selected=item.character;}
  await pet.waitForFunction(()=>window.petDiagnostics?.frames>5&&!window.petDiagnostics.loading);
  await panel.evaluate(playbackSpeed=>window.panel.command('settings',{playbackSpeed,transitionSpeed:1}),item.speed);
  const entry={id:'fx-loops',name:'原始特效倍速检查',steps:[{kind:'furniture',id:item.id,mode:'count',value:1,gap:0},{kind:'action',id:'interact',mode:'count',value:1,gap:0}]};
  await panel.evaluate(entry=>window.panel.command('preview',entry),entry);const start=Date.now();let seen=false,maxCached=0;
  while(true){const state=await panel.evaluate(()=>window.panel.state()),d=await pet.evaluate(()=>window.petDiagnostics);assert.equal(d.error,null);maxCached=Math.max(maxCached,d.cachedScenes);seen||=d.sceneAction===item.id;
   if(!state.playback&&seen)break;assert.ok(Date.now()-start<120000);await pet.waitForTimeout(200);
  }
  assert.equal(await pet.evaluate(()=>window.petDiagnostics.sceneKey),'model.glb');assert.ok(maxCached<=3);cycles.push({...item,seconds:(Date.now()-start)/1000,maxCached});console.log(item.character,item.speed,'complete');
 }
 assert.deepEqual(errors,[]);writeFileSync('test-results/newfx043-loops.json',JSON.stringify({complete:true,version:await app.evaluate(({app})=>app.getVersion()),cycles,errors},null,2));
}finally{await app.close();}
