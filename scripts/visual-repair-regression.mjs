import {openTestPanel} from './themed-menu-test-helper.mjs';
import {_electron as electron} from 'playwright';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const specs=JSON.parse(readFileSync('scripts/roster-wave12.json','utf8'));
const ids=process.argv.slice(2).length?process.argv.slice(2):Object.keys(specs).filter(id=>existsSync('.assets/wave12-ready/'+id+'/character.json'));
const root=path.resolve(process.env.BA_CHARACTERS||'.assets/repair-2026-10-28'),profile=path.resolve('test-results/visual-repair-preview-profile');mkdirSync(profile,{recursive:true});
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:ids[0],size:360,position:{x:450,y:180},eyeFollow:false}));
const env={...process.env,BA_CHARACTERS:root,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env});const results=[];
try{
 const page=await app.firstWindow();
 const panel=await openTestPanel(app,page);
 await app.evaluate(({screen})=>{screen.getCursorScreenPoint=()=>({x:-100000,y:-100000});});
 for(const character of ids){
  if(character!==ids[0]){const loaded=page.waitForEvent('load');await panel.evaluate(id=>window.panel.command('select',id),character);await loaded;}
  await page.waitForFunction(()=>window.petDiagnostics?.frames>10||window.petDiagnostics?.error);
  const diagnostics=await page.evaluate(()=>window.petDiagnostics);assert.equal(diagnostics.error,null,character);
  await page.screenshot({path:`test-results/repair-${character}-idle.png`,omitBackground:true});
  const cases=[];
  for(const action of ['interact','pickup']){
   await app.evaluate(({BrowserWindow},id)=>BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html')).webContents.send('pet:action',id),action);
   await page.evaluate(()=>window.petDiagnostics.measureFace=true);
   const samples=[];
   for(let i=0;i<12;i++){
    await page.waitForTimeout(250);const d=await page.evaluate(()=>window.petDiagnostics);
    assert.equal(d.error,null);if(character==='aoba'){const visible=[149,150,151].filter(n=>d.face['visible-'+n]?.[0]);assert.equal(visible.length,1,'Aoba must show exactly one authored face');}
    if(character==='chinatsu_onsen')assert.ok(Number.isFinite(d.mouthTile));samples.push({time:d.actionTime,mouth:d.mouthTile,action:d.action});
   }
   await page.screenshot({path:`test-results/repair-${character}-${action}.png`,omitBackground:true});cases.push({action,samples});
  }
  results.push({character,diagnostics,cases});console.log(character,'rendered');
 }
 writeFileSync('test-results/visual-repair-regression.json',JSON.stringify(results,null,2));
}finally{await app.close();}
