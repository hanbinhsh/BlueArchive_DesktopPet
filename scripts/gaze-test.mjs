import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const profile=path.resolve('test-results/gaze-profile');mkdirSync(profile,{recursive:true});writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'mutsuki_newyear',size:420,position:{x:100,y:100}}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env});
try{
 const page=await app.firstWindow();await page.waitForFunction(()=>window.petDiagnostics?.frames>5);
 await app.evaluate(({Menu})=>{Menu.prototype.popup=function(options){globalThis.testMenu=this;options?.callback?.();};});await page.evaluate(()=>window.pet.menu());
 const opened=app.waitForEvent('window');await app.evaluate(()=>globalThis.testMenu.getMenuItemById('open-panel').click());const panel=await opened;await panel.waitForSelector('#eyeFollow');
 await panel.locator('#eyeFollow').check();
 const directions=[];
 for(const direction of [-1,1]){
  await app.evaluate(({screen,BrowserWindow},direction)=>{const b=BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html')).getBounds();screen.getCursorScreenPoint=()=>({x:b.x+(direction<0?-500:b.width+500),y:b.y+100});},direction);
  await page.waitForTimeout(600);const gaze=await page.evaluate(()=>window.petDiagnostics.gaze);assert.ok(gaze.supported);assert.ok(gaze.direction[0]*direction>.8);directions.push(gaze);
  await page.screenshot({path:`test-results/gaze-${direction<0?'left':'right'}.png`,omitBackground:true});
 }
 await panel.locator('#testRandom').click();await page.waitForFunction(()=>window.petDiagnostics.action==='interact');assert.equal((await panel.evaluate(()=>window.panel.state())).settings.randomIdle,false);
 await page.waitForTimeout(100);assert.deepEqual((await page.evaluate(()=>window.petDiagnostics.gaze)).offsets,[]);
 await panel.locator('#stopTest').click();await page.waitForFunction(()=>window.petDiagnostics.action==='idle');
 await panel.locator('#testWalk').click();await page.waitForFunction(()=>window.petDiagnostics.action==='walk');
 assert.equal((await panel.evaluate(()=>window.panel.state())).settings.roaming,false);
 const before=await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html')).getBounds());await page.waitForTimeout(500);const after=await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html')).getBounds());assert.notEqual(before.x,after.x);
 await panel.locator('#stopTest').click();await page.waitForFunction(()=>window.petDiagnostics.action==='idle');
 await panel.locator('#eyeFollow').uncheck();await page.waitForTimeout(100);assert.deepEqual((await page.evaluate(()=>window.petDiagnostics.gaze)).offsets,[]);
 await panel.screenshot({path:'test-results/gaze-panel.png'});
 writeFileSync('test-results/gaze-tests.json',JSON.stringify({eyeFollow:true,directions,disableRestores:true,randomTest:true,walkTest:true,stopTest:true,togglesUnchanged:true,executable:process.env.BA_EXECUTABLE||'development'},null,2));console.log('Gaze and immediate test buttons passed');
}finally{await app.close();}
