import {openTestPanel} from './themed-menu-test-helper.mjs';
import {_electron as electron} from 'playwright';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(process.env.BA_CHARACTERS||'characters'),profile=path.resolve('test-results/furniture-audit-1105-profile');mkdirSync(profile,{recursive:true});
const rows=JSON.parse(readFileSync('test-results/furniture-audit-1105.json')).filter(r=>r.status==='ready'&&(!process.env.BA_PREVIEW_IDS||process.env.BA_PREVIEW_IDS.split(',').includes(r.character)));
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:rows[0].character,size:360,position:{x:450,y:180},eyeFollow:false}));
const env={...process.env,BA_CHARACTERS:root,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env}),results=[];
try{const page=await app.firstWindow();page.on('pageerror',e=>console.log('PAGEERROR',String(e)));page.on('console',e=>{if(e.type()==='error')console.log('CONSOLE',e.text().slice(0,600));});const panel=await openTestPanel(app,page);let selected=rows[0].character;
await app.evaluate(({ipcMain})=>{ipcMain.on('pet:playback-event',(_e,...a)=>console.log('PLAYBACK',...a));});
await app.evaluate(({screen})=>{screen.getCursorScreenPoint=()=>({x:-100000,y:-100000});});
for(const row of rows){
if(selected!==row.character){const loaded=page.waitForEvent('load');await panel.evaluate(id=>window.panel.command('select',id),row.character);await loaded;selected=row.character;}
await page.waitForFunction(()=>window.petDiagnostics?.frames>5&&!window.petDiagnostics.loading);
const c=JSON.parse(readFileSync(path.join(root,row.character,'character.json'))),f=c.furniture.find(f=>row.id?f.id===row.id:f.model===row.model);
await panel.evaluate(id=>window.panel.command('furniture',id),f.id);
try{await page.waitForFunction(id=>window.petDiagnostics?.sceneAction===id&&!window.petDiagnostics.loading,f.id,{timeout:20000});}catch(e){console.log('FAILED',await page.evaluate(()=>window.petDiagnostics),await panel.locator('body').innerText());throw e;}
assert.equal(await page.evaluate(()=>window.petDiagnostics.error),null);
for(const fraction of (row.times?row.times.map(t=>t/f.duration):[.02,.45,.85])){await page.evaluate(t=>{window.petDiagnostics.measurePose=true;window.petDiagnostics.seekTime=t;},f.duration*fraction);await page.waitForTimeout(180);await page.screenshot({path:`test-results/audit1105-${row.character}-${f.id}-${fraction}.png`,omitBackground:true});}
results.push({character:row.character,id:f.id,diagnostics:await page.evaluate(()=>window.petDiagnostics)});console.log(row.character,f.id);
await panel.evaluate(()=>window.panel.command('furniture',''));await page.waitForFunction(()=>window.petDiagnostics?.sceneKey==='model.glb'&&!window.petDiagnostics.loading);
}writeFileSync('test-results/furniture-audit-1105-runtime.json',JSON.stringify(results,null,2));}finally{await app.close();}
