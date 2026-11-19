import {_electron as electron} from 'playwright';
import {openTestPanel} from './themed-menu-test-helper.mjs';
import {mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const profile=path.resolve('test-results/outline-profile');mkdirSync(profile,{recursive:true});
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'neru_uniform',size:360,outline:false,eyeFollow:false}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const errors=[],results=[];
let app=await electron.launch({args:['.'],env});
try{
 const pet=await app.firstWindow(),panel=await openTestPanel(app,pet);
 pet.on('pageerror',e=>errors.push(String(e)));pet.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await app.evaluate(({screen})=>{screen.getCursorScreenPoint=()=>({x:-100000,y:-100000});});
 await pet.waitForFunction(()=>window.petDiagnostics?.frames>5&&!window.petDiagnostics.loading);
 await panel.locator('[data-page="appearance"]').click();
 const checkbox=panel.locator('#outline');await checkbox.check();
 assert.equal(await panel.locator('#outlineWidthNumber').inputValue(),'38');
 for(const width of [0,100,400,38]){await panel.locator('#outlineWidthNumber').fill(String(width));await pet.waitForTimeout(400);assert.equal(JSON.parse(readFileSync(path.join(profile,'settings.json'),'utf8')).outlineWidth,width);}
 assert.ok(await pet.evaluate(()=>window.petDiagnostics.outlineMeshes>0));
 await pet.waitForTimeout(400);
 await pet.screenshot({path:'test-results/outline-on.png',omitBackground:true});
 for(const enabled of [false,true,false,true]){
  await checkbox.setChecked(enabled);await pet.waitForTimeout(250);
  assert.equal(JSON.parse(readFileSync(path.join(profile,'settings.json'),'utf8')).outline,enabled);
  results.push(await pet.evaluate(()=>window.petDiagnostics));
 }
 assert.equal(results.at(-1).sceneLoads,results[0].sceneLoads,'toggling must not reload the model');
 await checkbox.uncheck();await pet.waitForTimeout(250);await pet.screenshot({path:'test-results/outline-off.png',omitBackground:true});
 await checkbox.check();await pet.waitForTimeout(250);
 await app.close();app=await electron.launch({args:['.'],env});
 const pet2=await app.firstWindow(),panel2=await openTestPanel(app,pet2);await panel2.locator('[data-page="appearance"]').click();assert.equal(await panel2.locator('#outline').isChecked(),true);assert.equal(await panel2.locator('#outlineWidthNumber').inputValue(),'38');
 assert.deepEqual(errors,[]);writeFileSync('test-results/outline-runtime.json',JSON.stringify({errors,results,restartPreserved:true},null,2));console.log('Outline toggling, model reuse and restart persistence passed');
}finally{await app.close();}
