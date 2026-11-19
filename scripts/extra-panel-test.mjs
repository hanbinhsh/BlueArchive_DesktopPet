import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync,readFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const executablePath=process.env.BA_EXECUTABLE;
assert.ok(executablePath,'Run against the packaged executable');
const added=Object.keys(JSON.parse(readFileSync('scripts/roster-extras.json','utf8')));
const profile=path.resolve('test-results/extra-panel-profile');mkdirSync(profile,{recursive:true});
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'midori_coat',size:360,position:{x:450,y:180}}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({executablePath,args:[],env});
const results=[];const errors=[];
try{
 const page=await app.firstWindow();page.on('pageerror',e=>errors.push(e.message));
 await page.waitForFunction(()=>window.petDiagnostics?.frames>5);
 await app.context().setOffline(true);
 await app.evaluate(({Menu,screen})=>{
  Menu.prototype.popup=function(options){globalThis.extraMenu=this;options?.callback?.();};
  globalThis.extraCursor={x:-100000,y:-100000};screen.getCursorScreenPoint=()=>globalThis.extraCursor;
 });
 await page.evaluate(()=>window.pet.menu());
 const event=app.waitForEvent('window');await app.evaluate(()=>globalThis.extraMenu.getMenuItemById('open-panel').click());
 const panel=await event;panel.on('pageerror',e=>errors.push(e.message));
 await panel.waitForSelector('.card');assert.equal(await panel.locator('.card').count(),65);
 await panel.waitForFunction(()=>[...document.querySelectorAll('.card img')].length===65&&[...document.querySelectorAll('.card img')].every(i=>i.complete&&i.naturalWidth>0));
 for(const character of added){
  const manifest=JSON.parse(readFileSync(`characters/${character}/character.json`,'utf8'));
  const card=panel.locator(`[data-character="${character}"]`);await card.scrollIntoViewIfNeeded();
  const before=await panel.evaluate(()=>scrollY);
  const loaded=page.waitForEvent('load');await card.click();await loaded;
  await page.waitForFunction(()=>window.petDiagnostics?.frames>5);
  await panel.waitForFunction(id=>document.querySelector(`[data-character="${id}"]`).getAttribute('aria-pressed')==='true'&&!document.querySelector('[data-action="idle"]').disabled,character);
  const after=await panel.evaluate(()=>scrollY);assert.ok(Math.abs(after-before)<=2,`${character}: scroll jumped ${before} -> ${after}`);
  assert.equal(await panel.locator('#characterNote').textContent(),manifest.note||'');
  assert.deepEqual((await panel.locator('[data-action]').evaluateAll(nodes=>nodes.map(n=>n.dataset.action))).sort(),manifest.actions.map(a=>a.id).sort());
  await panel.locator('[data-action="interact"]').click();await page.waitForFunction(()=>window.petDiagnostics.action==='interact');
  await panel.locator('[data-action="idle"]').click();await page.waitForFunction(()=>window.petDiagnostics.action==='idle');
  results.push({character,scrollBefore:before,scrollAfter:after,note:true,actionList:true});
 }
 const loaded=page.waitForEvent('load');await panel.locator('[data-character="midori_coat"]').click();await loaded;
 await page.waitForFunction(()=>window.petDiagnostics?.frames>5);
 await panel.waitForFunction(()=>!document.querySelector('#testWalk').disabled);
  const bounds=()=>app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html')).getBounds());
  const start=await bounds();
  await panel.locator('#testWalk').click();await page.waitForFunction(()=>window.petDiagnostics.action==='walk');
  await page.waitForTimeout(1200);const end=await bounds();assert.ok(Math.abs(start.x-end.x)>4,`Walk did not move: ${JSON.stringify({start,end})}`);
 await panel.locator('#stopTest').click();await page.waitForFunction(()=>window.petDiagnostics.action==='idle');
 await panel.locator('#testRandom').click();await page.waitForFunction(()=>window.petDiagnostics.action==='interact');
 await panel.locator('#stopTest').click();await page.waitForFunction(()=>window.petDiagnostics.action==='idle');
 await panel.screenshot({path:'test-results/extra-panel.png'});
 // Interrupt the long NPC interaction with a drag. No fabricated pickup clip exists.
 await panel.locator('[data-action="interact"]').click();await page.waitForFunction(()=>window.petDiagnostics.action==='interact');await panel.close();
 async function move(x,y){await app.evaluate(({BrowserWindow},p)=>{const b=BrowserWindow.getAllWindows()[0].getBounds();globalThis.extraCursor={x:b.x+p.x,y:b.y+p.y};},{x,y});await page.mouse.move(x,y);}
 let point;
 for(let y=100;y<430&&!point;y+=20)for(let x=150;x<400&&!point;x+=25){await move(x,y);await page.waitForTimeout(30);if(await page.evaluate(()=>window.petDiagnostics.hit))point={x,y};}
 assert.ok(point);assert.equal(await page.evaluate(()=>window.petDiagnostics.action),'interact');
 await page.mouse.down();await move(point.x+18,point.y+12);await page.waitForFunction(()=>window.petDiagnostics.action==='idle');
 const first=await page.evaluate(()=>window.petDiagnostics.frames);await page.waitForTimeout(1800);
 assert.ok(await page.evaluate(()=>window.petDiagnostics.frames)>first+30);assert.equal(await page.evaluate(()=>window.petDiagnostics.action),'idle');
 await page.mouse.up();assert.deepEqual(errors,[]);
 writeFileSync('test-results/extra-panel.json',JSON.stringify({executable:executablePath,offline:true,thumbnails:65,results,walk:true,randomTest:true,interruptNpcInteraction:true,errors},null,2));
 console.log('65 thumbnails, 8 notes/action lists, scroll retention, walking/random buttons and NPC interruption passed');
}finally{await app.close();}
