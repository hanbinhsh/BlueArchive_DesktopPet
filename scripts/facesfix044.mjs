import {openTestPanel} from './themed-menu-test-helper.mjs';
import {_electron as electron} from 'playwright';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const names=['chiaki'];
const root=path.resolve(process.env.BA_CHARACTERS||'characters'),profile=path.resolve('test-results/facesfix044-profile');mkdirSync(profile,{recursive:true});
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:names[0],size:360,yaw:0,pitch:0,roll:0,eyeFollow:false,allowOffscreen:true,randomIdle:false,roaming:false,position:{x:400,y:180}}));
const env={...process.env,BA_TEST_DATA:profile,BA_CHARACTERS:root};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[],env}),results=[],errors=[];
try{
 const pet=await app.firstWindow();await app.context().setOffline(true);pet.on('pageerror',e=>errors.push(String(e)));const panel=await openTestPanel(app,pet);await app.evaluate(({BrowserWindow})=>{const w=BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html'));w.setFocusable(false);w.setBounds({...w.getBounds(),x:-4000,y:180});});
 await app.evaluate(({screen})=>{screen.getCursorScreenPoint=()=>({x:-99999,y:-99999});});let selected=names[0];
 for(const name of names){
  if(selected!==name){const loaded=pet.waitForEvent('load');await panel.evaluate(id=>window.panel.command('select',id),name);await loaded;selected=name;}
  await pet.waitForFunction(()=>window.petDiagnostics?.frames>5&&!window.petDiagnostics.loading);
  const c=JSON.parse(readFileSync(path.join(root,name,'character.json'),'utf8')),samples=[];
  for(const id of ['idle','interact','pickup'].filter(id=>id==='idle'||c.actions.some(a=>a.id===id))){
   await pet.evaluate(()=>{delete window.petDiagnostics.freezeTime;window.petDiagnostics.measureFace=true;});
   await app.evaluate(({BrowserWindow},id)=>BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html')).webContents.send('pet:action',id),id);
   await pet.waitForFunction(id=>window.petDiagnostics.action===id&&!window.petDiagnostics.loading,id);
   const duration=await pet.evaluate(id=>window.petDiagnostics.durations[id],id);assert.ok(duration>0);
   for(const fraction of [0,.33,.66]){
    await pet.evaluate(t=>{window.petDiagnostics.freezeTime=t;},duration*fraction);await pet.waitForTimeout(140);
    const d=await pet.evaluate(()=>window.petDiagnostics);assert.equal(d.error,null);assert.ok(Object.values(d.face).flat().every(Number.isFinite));
    if(c.mouth){assert.ok(d.mouthMaps.length);assert.ok(d.mouthMaps.every(m=>m.offset.every(Number.isFinite)));}
    await pet.screenshot({path:`test-results/facesfix044-${name}-${id}-${fraction}.png`,omitBackground:true});samples.push({id,fraction,mouthTile:d.mouthTile,mouthMaps:d.mouthMaps,face:d.face});
   }
  }
  results.push({character:name,samples});console.log(name,'face and prop samples',samples.length);
 }
 assert.deepEqual(errors,[]);writeFileSync('test-results/facesfix044-runtime.json',JSON.stringify({complete:true,results,errors},null,2));
}finally{await app.close();}
