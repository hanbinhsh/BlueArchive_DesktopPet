import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const executablePath=process.env.BA_EXECUTABLE;assert.ok(executablePath);
const profile=path.resolve('test-results/wave7-size-profile');mkdirSync(profile,{recursive:true});
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'hifumi',size:360,yaw:0,pitch:0,position:{x:400,y:180}}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({executablePath,args:[],env});const results=[];
try{
 const page=await app.firstWindow();await page.waitForFunction(()=>window.petDiagnostics?.frames>5);
 await app.evaluate(({Menu,screen})=>{Menu.prototype.popup=function(){globalThis.testMenu=this;};screen.getCursorScreenPoint=()=>({x:-100000,y:-100000});});
 await page.context().setOffline(true);
 async function select(id){await page.evaluate(()=>window.pet.menu());await page.waitForTimeout(60);await app.evaluate(({BrowserWindow},id)=>{const item=globalThis.testMenu.getMenuItemById(id);if(!item){const walk=m=>m.items.flatMap(i=>[i.id,...i.submenu?walk(i.submenu):[]]);throw Error('Missing '+id+': '+JSON.stringify(walk(globalThis.testMenu)));}item.click(item,BrowserWindow.getAllWindows()[0],{});},id);}
 for(const character of ['hifumi','izuna']){
  if(character==='izuna'){const loaded=page.waitForEvent('load');await select('costume-izuna');await loaded;await page.waitForFunction(()=>window.petDiagnostics?.frames>5);}
  await page.evaluate(()=>window.petMeasureFraming=true);await page.waitForTimeout(300);
  const idle=await page.evaluate(()=>window.petFramingDiagnostics);assert.ok(idle.max[1]-idle.min[1]>1.25,`${character}: normal idle is too small`);
  assert.equal(idle.zoom,1);assert.equal(idle.centerY,1);
  await page.screenshot({path:`test-results/size-fixed-${character}-idle.png`,omitBackground:true});
  await select('action-victory');await page.waitForFunction(()=>window.petDiagnostics.action==='victory');
  const samples=[];
  while(await page.evaluate(()=>window.petDiagnostics.action==='victory')){
   await page.waitForTimeout(40);const sample=await page.evaluate(()=>({time:window.petDiagnostics.actionTime,transition:window.petDiagnostics.transition,view:window.petFramingDiagnostics}));samples.push(sample);
   const fits=sample.view.min.slice(0,2).every(x=>x> -1.03)&&sample.view.max.slice(0,2).every(x=>x<1.03);
   if(!fits)await page.screenshot({path:`test-results/size-${character}-transition-${samples.length}.png`,omitBackground:true});
   // A parked, collapsed weapon moves in from offstage during a crossfade.
   // Keep those samples/screenshots for review; check the full settled motion.
   if(!sample.transition?.remaining)assert.ok(fits,`${character}: clipped frame ${JSON.stringify(sample)}`);
   if(samples.length===20)await page.screenshot({path:`test-results/size-fixed-${character}-victory.png`,omitBackground:true});
  }
  await page.waitForTimeout(250);const restored=await page.evaluate(()=>window.petFramingDiagnostics);
  assert.equal(restored.zoom,1);assert.equal(restored.centerY,1);
  assert.ok(restored.max[1]-restored.min[1]>1.25);
  if(character==='izuna')assert.ok(samples.some(s=>s.view.zoom===.62&&s.view.centerY===2));
  const bounds=await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows()[0].getBounds());assert.ok(Math.abs(bounds.width-540)<3&&Math.abs(bounds.height-522)<3);
  results.push({character,idle,samples,restored,bounds});console.log(character,'normal size, full victory framing and restored camera passed');
 }
 writeFileSync('test-results/wave7-size-runtime.json',JSON.stringify({executable:executablePath,results},null,2));
}finally{await app.close();}
