import { _electron as electron } from 'playwright';
import { mkdirSync, writeFileSync, readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const profile = path.resolve('test-results/furniture-profile'); mkdirSync(profile,{recursive:true});
const root=process.env.BA_CHARACTERS||(process.env.BA_EXECUTABLE?path.join(path.dirname(process.env.BA_EXECUTABLE),'resources/characters'):'characters');
const reportPrefix=process.env.BA_FURNITURE_REPORT||'furniture-runtime';
const roster = readdirSync(root,{withFileTypes:true}).filter(d=>d.isDirectory()).map(d=>d.name).filter(id=>process.argv.length<=2||process.argv.slice(2).includes(id)).filter(id=>JSON.parse(readFileSync(path.join(root,id,'character.json'),'utf8')).furniture?.length);
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:roster[0],size:420,position:{x:450,y:160}}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env});
const results=process.env.BA_FURNITURE_UPDATE ? JSON.parse(readFileSync(`test-results/${reportPrefix}.json`,'utf8')).filter(r=>!roster.includes(r.character)) : [];
writeFileSync(`test-results/${reportPrefix}-run.json`,JSON.stringify({executable:process.env.BA_EXECUTABLE||'development',root,started:new Date().toISOString(),complete:false},null,2));
try {
 const page=await app.firstWindow();
 await app.evaluate(({Menu,screen})=>{Menu.prototype.popup=function(){globalThis.testMenu=this;};globalThis.testCursor={x:-10000,y:-10000};screen.getCursorScreenPoint=()=>globalThis.testCursor;});
 async function ready(){await page.waitForFunction(()=>window.petDiagnostics?.error||window.petDiagnostics?.frames>5,null,{timeout:60000});assert.equal(await page.evaluate(()=>window.petDiagnostics.error),null);}
 async function select(id){await page.evaluate(()=>window.pet.menu());await app.evaluate(({BrowserWindow},id)=>{const m=globalThis.testMenu.getMenuItemById(id);if(!m||!m.enabled)throw Error('Missing/disabled '+id);m.click(m,BrowserWindow.getAllWindows()[0],{});},id);}
 async function reload(id){const wait=page.waitForEvent('load');await select(id);await wait;await ready();}
 await ready(); await page.context().setOffline(true);
 for(const character of roster){
  if(character!==roster[0])await reload('costume-'+character);
  const {character:spec}=await page.evaluate(()=>window.pet.init());
  for(const f of spec.furniture){
   if(process.env.BA_FURNITURE_FILTER&&!f.id.includes(process.env.BA_FURNITURE_FILTER))continue;
   await reload('furniture-'+f.id);
   assert.equal((await page.evaluate(()=>window.pet.init())).furniture.id,f.id);
   await page.evaluate(()=>window.petDiagnostics.measureFace=true);
   const samples=[];
   for(let i=0;i<3;i++){
    await page.waitForTimeout(i?900:100);
    samples.push(await page.evaluate(()=>({frames:window.petDiagnostics.frames,time:window.petDiagnostics.actionTime,mouth:window.petDiagnostics.mouthTile,face:window.petDiagnostics.face})));
    await page.screenshot({path:`test-results/furniture-${character}-${f.id}-${i}.png`,omitBackground:true});
   }
   assert.ok(samples[2].frames>samples[0].frames+20);assert.ok(Math.abs(samples[2].time-samples[0].time)>.05);
   for(const phase of [.25,.5,.75,.97]){await page.evaluate(t=>window.petDiagnostics.seekTime=t,f.duration*phase);await page.waitForTimeout(80);await page.screenshot({path:`test-results/furniture-${character}-${f.id}-phase${phase}.png`,omitBackground:true});}
   if(process.env.BA_FURNITURE_ANGLES){
    for(const angle of [0,.5,1,1.5]){
     await page.evaluate(({a,yaw})=>{window.pet.rotate(a*Math.PI-yaw,0);window.pet.resize(420);window.petDiagnostics.seekTime=2;},{a:angle,yaw:f.yaw??Math.PI*.75});
     await page.waitForTimeout(150);await page.screenshot({path:`test-results/furniture-${character}-${f.id}-angle${angle}.png`,omitBackground:true});
    }
    await page.evaluate(()=>{window.pet.rotate(0,0);window.pet.resize(420);});
   }
   await reload('furniture-close');
   assert.equal((await page.evaluate(()=>window.pet.init())).furniture,undefined);
   assert.equal(await page.evaluate(()=>window.petDiagnostics.action),'idle');
   results.push({character,furniture:f.id,duration:f.duration,samples});
   writeFileSync(`test-results/${reportPrefix}.json`,JSON.stringify(results,null,2));
   console.log('PASS',character,f.id);
  }
 }
 writeFileSync(`test-results/${reportPrefix}-run.json`,JSON.stringify({executable:process.env.BA_EXECUTABLE||'development',root,completed:new Date().toISOString(),complete:true,offline:true,count:results.length},null,2));
} finally{await app.close();}
