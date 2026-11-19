import {openTestPanel} from './themed-menu-test-helper.mjs';
import {_electron as electron} from 'playwright';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(process.env.BA_CHARACTERS||'.assets/repair-2026-10-29'),profile=path.resolve('test-results/furniture-sweep-1029-profile');mkdirSync(profile,{recursive:true});
const rows=JSON.parse(readFileSync('test-results/furniture-view-review-1030.json')).filter(r=>r.status==='ready'&&(!process.env.BA_PREVIEW_IDS||process.env.BA_PREVIEW_IDS.split(',').includes(r.character)));
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:rows[0].character,size:360,position:{x:450,y:180},eyeFollow:false}));
const env={...process.env,BA_CHARACTERS:root,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env}),results=[];
try{const page=await app.firstWindow(),panel=await openTestPanel(app,page);let selected=rows[0].character;
await app.evaluate(({screen})=>{screen.getCursorScreenPoint=()=>({x:-100000,y:-100000});});
for(const row of rows){
if(selected!==row.character){const loaded=page.waitForEvent('load');await panel.evaluate(id=>window.panel.command('select',id),row.character);await loaded;selected=row.character;}
await page.waitForFunction(()=>window.petDiagnostics?.frames>5&&!window.petDiagnostics.loading);
const c=JSON.parse(readFileSync(path.join(root,row.character,'character.json'))),f=c.furniture.find(f=>row.id?f.id===row.id:f.model===row.model);
await panel.evaluate(id=>window.panel.command('furniture',id),f.id);
await page.waitForFunction(id=>window.petDiagnostics?.sceneAction===id&&!window.petDiagnostics.loading,f.id,{timeout:20000});
assert.equal(await page.evaluate(()=>window.petDiagnostics.error),null);
for(const yaw of [0,.25,.5,.75,1,1.25,1.5,1.75]){await panel.evaluate(yaw=>window.panel.command('settings',{yaw}),yaw*Math.PI-(f.yaw??Math.PI*.75));await page.evaluate(t=>window.petDiagnostics.seekTime=t,f.duration*.2);await page.waitForTimeout(120);await page.screenshot({path:`test-results/sweep1030-${row.character}-${f.id}-${yaw}.png`,omitBackground:true});}
results.push({character:row.character,id:f.id,diagnostics:await page.evaluate(()=>window.petDiagnostics)});console.log(row.character,f.id);
await panel.evaluate(()=>window.panel.command('furniture',''));await page.waitForFunction(()=>window.petDiagnostics?.sceneKey==='model.glb'&&!window.petDiagnostics.loading);
}writeFileSync('test-results/furniture-sweep-1029-runtime.json',JSON.stringify(results,null,2));}finally{await app.close();}
