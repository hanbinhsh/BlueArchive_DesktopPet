import {openTestPanel} from './themed-menu-test-helper.mjs';
import {_electron as electron} from 'playwright';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(process.env.BA_CHARACTERS||'.assets/repair-2026-10-29'),profile=path.resolve('test-results/stable-026-profile');mkdirSync(profile,{recursive:true});
const rows=JSON.parse(readFileSync('test-results/stable-026.json')).filter(r=>r.status==='ready'&&(!process.env.BA_PREVIEW_IDS||process.env.BA_PREVIEW_IDS.split(',').includes(r.character)));
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:rows[0].character,size:360,position:{x:450,y:180},eyeFollow:false}));
const env={...process.env,BA_CHARACTERS:root,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env}),results=[];
try{await app.context().setOffline(true);const page=await app.firstWindow(),panel=await openTestPanel(app,page);let selected=rows[0].character;
await app.evaluate(({screen})=>{screen.getCursorScreenPoint=()=>({x:-100000,y:-100000});});
for(const row of rows){
if(selected!==row.character){const loaded=page.waitForEvent('load');await panel.evaluate(id=>window.panel.command('select',id),row.character);await loaded;selected=row.character;}
await page.waitForFunction(()=>window.petDiagnostics?.frames>5&&!window.petDiagnostics.loading);
const c=JSON.parse(readFileSync(path.join(root,row.character,'character.json'))),f=c.furniture.find(f=>row.id?f.id===row.id:f.model===row.model);
await panel.evaluate(id=>window.panel.command('furniture',id),f.id);
await page.waitForFunction(id=>window.petDiagnostics?.sceneAction===id&&!window.petDiagnostics.loading,f.id,{timeout:20000});
assert.equal(await page.evaluate(()=>window.petDiagnostics.error),null);
for(const fraction of [.1,.5,.9]){await page.evaluate(t=>window.petDiagnostics.seekTime=t,f.duration*fraction);await page.waitForTimeout(180);await page.screenshot({path:`test-results/stable026-${row.character}-${f.id}-${fraction}.png`,omitBackground:true});}
const maps=await page.evaluate(()=>window.petDiagnostics.mouthMaps);assert.equal(new Set(maps.map(m=>m.texture)).size,maps.length);results.push({character:row.character,id:f.id,diagnostics:await page.evaluate(()=>window.petDiagnostics)});console.log(row.character,f.id);
await panel.evaluate(()=>window.panel.command('furniture',''));await page.waitForFunction(()=>window.petDiagnostics?.sceneKey==='model.glb'&&!window.petDiagnostics.loading);
}writeFileSync('test-results/stable-026-runtime.json',JSON.stringify(results,null,2));}finally{await app.close();}
