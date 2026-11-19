import { _electron as electron } from 'playwright';
import { mkdirSync, writeFileSync, readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const profile=path.resolve('test-results/furniture-views-profile');mkdirSync(profile,{recursive:true});
const roster=readdirSync('characters',{withFileTypes:true}).filter(d=>d.isDirectory()).map(d=>JSON.parse(readFileSync(`characters/${d.name}/character.json`,'utf8'))).filter(c=>c.furniture?.length&&(process.argv.length<=2||process.argv.slice(2).includes(c.id)));
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:roster[0].id,size:420,position:{x:450,y:160}}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({args:['.'],env});const seen=new Set(),output=[];
try {
 const page=await app.firstWindow();
 await app.evaluate(({Menu,screen})=>{Menu.prototype.popup=function(){globalThis.testMenu=this;};screen.getCursorScreenPoint=()=>({x:-10000,y:-10000});});
 const ready=async()=>{await page.waitForFunction(()=>window.petDiagnostics?.error||window.petDiagnostics?.frames>2);assert.equal(await page.evaluate(()=>window.petDiagnostics.error),null);};
 const select=async id=>{await page.evaluate(()=>window.pet.menu());const wait=page.waitForEvent('load');await app.evaluate(({BrowserWindow},id)=>{const m=globalThis.testMenu.getMenuItemById(id);m.click(m,BrowserWindow.getAllWindows()[0],{});},id);await wait;await ready();};
 await ready();
 for(const c of roster){
  if(c.id!==roster[0].id)await select('costume-'+c.id);
  for(const f of c.furniture){
   const id=f.id.split('_')[0];if(seen.has(id))continue;seen.add(id);
   await select('furniture-'+f.id);
   for(const a of [0,.5,1,1.5]){
    await page.evaluate(({a,yaw})=>{window.pet.rotate(a*Math.PI-yaw,0);window.pet.resize(420);window.petDiagnostics.seekTime=2;},{a,yaw:f.yaw??Math.PI*.75});
    await page.waitForTimeout(160);
    await page.screenshot({path:`test-results/view-${c.id}-${f.id}-${a}.png`,omitBackground:true});
   }
   output.push({character:c.id,id:f.id});console.log('VIEW',c.id,f.id);
   await page.evaluate(()=>window.pet.rotate(0,0));await select('furniture-close');
  }
 }
 writeFileSync('test-results/furniture-views.json',JSON.stringify(output,null,2));
}finally{await app.close();}
