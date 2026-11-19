import { _electron as electron } from 'playwright';
import { mkdirSync, writeFileSync, readFileSync, copyFileSync } from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const profile=path.resolve('test-results/furniture-controls-profile');mkdirSync(profile,{recursive:true});
const character=process.env.BA_TEST_CHARACTER||'hoshino',furniture=process.env.BA_TEST_FURNITURE||'f11205_0';
const resourceRoot=process.env.BA_CHARACTERS||(process.env.BA_EXECUTABLE?path.join(path.dirname(process.env.BA_EXECUTABLE),'resources/characters'):'characters');
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character,size:360,position:{x:450,y:160},randomIdle:true,roaming:true}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env});
const result={executable:process.env.BA_EXECUTABLE||'development'};
try{
 const page=await app.firstWindow();await page.waitForFunction(()=>window.petDiagnostics?.frames>5);
 await app.evaluate(({Menu,screen})=>{Menu.prototype.popup=function(){globalThis.testMenu=this;};globalThis.testCursor={x:-10000,y:-10000};screen.getCursorScreenPoint=()=>globalThis.testCursor;});
 async function select(id){await page.evaluate(()=>window.pet.menu());await app.evaluate(({BrowserWindow},id)=>{const i=globalThis.testMenu.getMenuItemById(id);assertEnabled(i,id);i.click(i,BrowserWindow.getAllWindows()[0],{});function assertEnabled(i,id){if(!i||!i.enabled)throw Error('Disabled '+id);}},id);}
 async function load(id){const loaded=page.waitForEvent('load');await select(id);await loaded;await page.waitForFunction(()=>window.petDiagnostics?.frames>5||window.petDiagnostics?.error);assert.equal(await page.evaluate(()=>window.petDiagnostics.error),null);}
 await load('furniture-'+furniture);
 await page.evaluate(()=>window.petDiagnostics.seekTime=2);await page.waitForTimeout(100);
 let point;
 async function move(x,y){await app.evaluate(({BrowserWindow},p)=>{const b=BrowserWindow.getAllWindows()[0].getBounds();globalThis.testCursor={x:b.x+p.x,y:b.y+p.y};},{x,y});await page.mouse.move(x,y);await page.waitForTimeout(40);}
 const viewport=page.viewportSize()||await page.evaluate(()=>({width:innerWidth,height:innerHeight}));
 for(let y=viewport.height*.4;y<viewport.height*.9&&!point;y+=25)for(let x=viewport.width*.25;x<viewport.width*.8;x+=25){await move(x,y);if(await page.evaluate(()=>window.petDiagnostics.hit)){point={x,y};break;}}
 assert.ok(point,'Furniture must receive mouse hits');
 const before=await page.evaluate(()=>({frames:window.petDiagnostics.frames,time:window.petDiagnostics.actionTime}));
 await page.mouse.down();await move(point.x+30,point.y+15);await page.waitForTimeout(2400);
 assert.equal(await page.evaluate(()=>window.petDiagnostics.action),'idle');
 assert.ok(await page.evaluate(n=>window.petDiagnostics.frames>n+30,before.frames));
 const heldTime=await page.evaluate(()=>window.petDiagnostics.actionTime);assert.ok(heldTime>before.time+1.5);
 await page.mouse.up();await page.waitForTimeout(100);assert.ok(await page.evaluate(t=>window.petDiagnostics.actionTime>=t,heldTime));result.dragKeepsFurniturePlaying=true;
 // The animated character may have left the original hit point while held.
 point=undefined;
 for(let y=viewport.height*.4;y<viewport.height*.9&&!point;y+=25)for(let x=viewport.width*.25;x<viewport.width*.8;x+=25){await move(x,y);if(await page.evaluate(()=>window.petDiagnostics.hit)){point={x,y};break;}}
 assert.ok(point,'Furniture remains hittable after dragging');await page.mouse.click(point.x,point.y);await page.waitForTimeout(100);assert.ok(await page.evaluate(()=>window.petDiagnostics.actionTime<1));result.clickRestarts=true;
 const duration=(await page.evaluate(()=>window.pet.init())).furniture.duration;await page.evaluate(t=>window.petDiagnostics.seekTime=t,duration-.2);await page.waitForTimeout(650);assert.ok(await page.evaluate(()=>window.petDiagnostics.actionTime<1));result.animationLoops=true;
 await move(2,2);assert.equal(await page.evaluate(()=>window.petDiagnostics.hit),false);result.blankPassThrough=true;
 await select('view-down');await page.waitForTimeout(100);const orientation=await page.evaluate(()=>window.petDiagnostics.orientation);assert.ok(Math.abs(orientation[0]-Math.PI/12)<.001);result.rotation=true;
 await page.evaluate(()=>window.pet.resize(400));await page.waitForTimeout(150);const bounds=await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows()[0].getBounds());assert.ok(Math.abs(bounds.width-600)<=1,'DPI rounding must stay within one DIP');result.resize=true;
 await page.evaluate(()=>window.pet.menu());const menu=await app.evaluate(()=>globalThis.testMenu.items.find(i=>i.label==='始终置顶').checked);assert.equal(menu,true);
 await app.evaluate(()=>{const i=globalThis.testMenu.items.find(i=>i.label==='始终置顶');i.click(i);});await page.waitForTimeout(150);
 assert.equal(await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows()[0].isAlwaysOnTop()),false);
 await app.evaluate(()=>{const i=globalThis.testMenu.items.find(i=>i.label==='始终置顶');i.click(i);});result.alwaysOnTop=true;
 // UI offers the new section, keeps normal actions disabled during furniture,
 // and restores the previous automatic-activity preferences on closing it.
 const panelPromise=app.waitForEvent('window');await select('open-panel');const panel=await panelPromise;await panel.waitForSelector('#furniture button');
 assert.ok(await panel.locator('#actions .play').first().isDisabled());await panel.locator('#closeFurniture').click();await page.waitForFunction(async()=>!(await window.pet.init()).furniture&&window.petDiagnostics.frames>5);
 assert.equal((await page.evaluate(()=>window.pet.init())).settings.randomIdle,true);assert.equal((await page.evaluate(()=>window.pet.init())).settings.roaming,true);result.panelAndRestore=true;
}finally{await app.close();}
// Deliberately corrupt a copy, never the user's installed resources.
const root=path.resolve('test-results/furniture-broken-'+character);const dir=path.join(root,character);mkdirSync(dir,{recursive:true});
const spec=JSON.parse(readFileSync(path.join(resourceRoot,character,'character.json'),'utf8'));writeFileSync(path.join(dir,'character.json'),JSON.stringify(spec));copyFileSync(path.join(resourceRoot,character,'model.glb'),path.join(dir,'model.glb'));
const bad=Buffer.from(readFileSync(path.join(resourceRoot,character,spec.furniture[0].model)));bad[20]=0;writeFileSync(path.join(dir,spec.furniture[0].model),bad);
const broken=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env:{...env,BA_CHARACTERS:root}});
try{
 const p=await broken.firstWindow();await p.waitForFunction(()=>window.petDiagnostics?.frames>5);await broken.evaluate(({Menu})=>{Menu.prototype.popup=function(){globalThis.testMenu=this;};});
 async function click(id){await p.evaluate(()=>window.pet.menu());await broken.evaluate(({BrowserWindow},id)=>{const i=globalThis.testMenu.getMenuItemById(id);if(!i?.enabled)throw Error(id);i.click(i,BrowserWindow.getAllWindows()[0],{});},id);}
 const failed=p.waitForEvent('load');await click('furniture-'+spec.furniture[0].id);await failed;await p.waitForFunction(()=>!!window.petDiagnostics?.error);assert.ok(await p.locator('#status').isVisible());
 const recovered=p.waitForEvent('load');await click('furniture-close');await recovered;await p.waitForFunction(()=>window.petDiagnostics?.frames>5);assert.equal(await p.evaluate(()=>window.petDiagnostics.error),null);result.corruptModelRecovery=true;
}finally{await broken.close();}
writeFileSync(`test-results/${process.env.BA_CONTROL_REPORT||'furniture-controls'}.json`,JSON.stringify(result,null,2));console.log(result);
