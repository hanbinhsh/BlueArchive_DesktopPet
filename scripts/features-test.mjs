import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync,readFileSync,readdirSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const rosterCount=readdirSync('characters',{withFileTypes:true}).filter(x=>x.isDirectory()).length;
const profile=path.resolve('test-results/features-profile');mkdirSync(profile,{recursive:true});
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'iori',size:280,yaw:0,pitch:0,position:{x:120,y:200}}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const launch=()=>electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env});
let app=await launch();let page=await app.firstWindow();const errors=[];page.on('pageerror',e=>errors.push(e.message));
async function openPanel(){
 await app.evaluate(({Menu})=>{Menu.prototype.popup=function(options){globalThis.testMenu=this;options?.callback?.();};});
 await page.evaluate(()=>window.pet.menu());
 const event=app.waitForEvent('window');await app.evaluate(()=>globalThis.testMenu.getMenuItemById('open-panel').click());const p=await event;await p.waitForSelector('[data-character="iori"]');return p;
}
try{
 await page.waitForFunction(()=>window.petDiagnostics?.frames>5);let panel=await openPanel();
 assert.equal(await panel.locator('.card').count(),rosterCount);
 assert.equal(await panel.locator('.card img').count(),rosterCount);
 await panel.locator('#search').fill('睦月');assert.equal(await panel.locator('.card').count(),3);await panel.locator('#search').fill('');
 const loaded=page.waitForEvent('load');await panel.locator('[data-character="mutsuki_dress"]').click();await loaded;await page.waitForFunction(()=>window.petDiagnostics?.frames>5);
 await panel.locator('[data-action="interact"]').click();await page.waitForFunction(()=>window.petDiagnostics.action==='interact');
 await panel.locator('[data-favorite="interact"]').click();await panel.locator('#onlyFavorites').check();assert.equal(await panel.locator('.play').count(),1);
 await panel.screenshot({path:'test-results/features-panel.png'});
 await panel.locator('#onlyFavorites').uncheck();
 // Panel blocks automation even while enabled.
 await panel.locator('#randomInterval').selectOption('15');await panel.locator('#randomIdle').check();
 await page.waitForFunction(()=>window.petDiagnostics.action==='idle');await page.waitForTimeout(18000);assert.equal(await page.evaluate(()=>window.petDiagnostics.action),'idle');
 await panel.close();await page.mouse.move(5,5);await page.waitForFunction(()=>window.petDiagnostics.action==='interact',null,{timeout:25000});
 console.log('Panel, grouping, previews, favorites and random idle passed');
 panel=await openPanel();await panel.locator('#randomIdle').uncheck();
 await panel.locator('[data-action="idle"]').click();await page.waitForFunction(()=>window.petDiagnostics.action==='idle');
 await panel.locator('#roamRadius').selectOption('80');await panel.locator('#roamSpeed').selectOption('20');await panel.locator('#roaming').check();
 await app.evaluate(()=>{Math.random=()=>0.9;});
 const before=await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html')).getBounds());
 await panel.close();await page.mouse.move(5,5);await page.waitForFunction(()=>window.petDiagnostics.action==='walk',null,{timeout:25000});
 const samples=[];for(let i=0;i<10;i++){await page.waitForTimeout(150);samples.push(await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows()[0].getBounds()));}
 assert.ok(samples.at(-1).x>samples[0].x);for(const b of samples){assert.ok(Math.abs(b.x-before.x)<=81);assert.ok(Math.abs(b.width-before.width)<=1);assert.ok(Math.abs(b.height-before.height)<=1);}
 // Explicit interaction cancels walking immediately; it stays idle afterward.
 let point; for(let y=120;y<=300&&!point;y+=30)for(let x=160;x<=260&&!point;x+=25){await page.mouse.move(x,y);await page.waitForTimeout(25);if(await page.evaluate(()=>window.petDiagnostics.hit))point={x,y};}
 assert.ok(point,'Hover finds the walking character');await page.waitForFunction(()=>window.petDiagnostics.action==='idle');
 await page.mouse.down();await page.mouse.move(point.x+18,point.y+12,{steps:3});await page.waitForFunction(()=>window.petDiagnostics.action==='pickup');await page.mouse.up();await page.waitForFunction(()=>window.petDiagnostics.action==='idle');
 const stopped=await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows()[0].getBounds());await page.waitForTimeout(1200);
 assert.equal((await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows()[0].getBounds())).x,stopped.x);
 console.log('Bounded walking, fixed window size and manual interruption passed');
 panel=await openPanel();await panel.locator('#roaming').uncheck();
 await panel.locator('[data-character="plana"]').click();await page.waitForFunction(()=>window.petDiagnostics?.animations?.some(n=>n.includes('AroPla'))||window.petDiagnostics?.bones>200);
 assert.match(await panel.locator('#walkHint').textContent(),/没有可用/);
 await panel.close();await page.waitForTimeout(400);await app.close();
 app=await launch();page=await app.firstWindow();await page.waitForFunction(()=>window.petDiagnostics?.frames>5);
 const restored=await page.evaluate(()=>window.pet.init());assert.equal(restored.settings.character,'plana');assert.ok(restored.settings.favorites.includes('mutsuki_dress:interact'));assert.equal(restored.settings.roamRadius,80);assert.equal(restored.settings.roaming,false);
 assert.deepEqual(errors,[]);
 writeFileSync('test-results/features.json',JSON.stringify({panel:true,grouping:true,thumbnails:rosterCount,preview:true,favorites:true,randomIdle:true,panelPause:true,walk:true,manualInterruption:true,hoverPause:true,dragOverridesWalk:true,bounds:samples,restart:true,executable:process.env.BA_EXECUTABLE||'development'},null,2));
 console.log('All feature checks passed');
}finally{await app.close();}
