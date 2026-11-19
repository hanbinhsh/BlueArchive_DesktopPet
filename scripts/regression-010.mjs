import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const profile=path.resolve('test-results/regression-010-profile');mkdirSync(profile,{recursive:true});
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'iori',size:280,yaw:0,pitch:.3,position:{x:150,y:150}}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env});
try{
 const page=await app.firstWindow();await page.waitForFunction(()=>window.petDiagnostics?.frames>5);
 await app.evaluate(({Menu})=>{Menu.prototype.popup=function(options){globalThis.testMenu=this;options?.callback?.();};});
 await page.evaluate(()=>window.pet.menu());const opened=app.waitForEvent('window');await app.evaluate(()=>globalThis.testMenu.getMenuItemById('open-panel').click());const panel=await opened;await panel.waitForSelector('[data-character="reisa"]');
 await panel.locator('[data-character="reisa"]').scrollIntoViewIfNeeded();
 const before=await panel.evaluate(()=>window.scrollY);assert.ok(before>200);
 await panel.locator('[data-character="reisa"]').click();
 await page.waitForFunction(()=>window.petDiagnostics?.animations?.some(n=>n.startsWith('CH0167_'))&&window.petDiagnostics.frames>5);
 await panel.waitForTimeout(300);const after=await panel.evaluate(()=>window.scrollY);assert.ok(Math.abs(after-before)<4,`Scroll jumped: ${before} -> ${after}`);
 await panel.locator('#roamRadius').selectOption('4000');
 assert.equal((await panel.evaluate(()=>window.panel.state())).settings.roamRadius,4000);
 await app.evaluate(({screen,BrowserWindow})=>{const b=BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html')).getBounds();screen.getCursorScreenPoint=()=>({x:b.x-100,y:b.y-100});});
 await page.waitForTimeout(150);
 const yaw=await page.evaluate(()=>window.petDiagnostics.orientation[1]);
 await panel.locator('#testWalk').click();const turn=[];
 for(let i=0;i<20;i++){turn.push((await page.evaluate(()=>window.petDiagnostics.orientation))[1]);await page.waitForTimeout(20);}
 assert.ok(new Set(turn.map(v=>v.toFixed(3))).size>=3,'Turn must contain intermediate poses');
 assert.ok(Math.abs(turn[0]-yaw)<1,'Turn must not instantly snap 90 degrees');
 assert.ok(Math.abs(turn.at(-1)-yaw)>1.4,'Turn reaches walking direction');
 await panel.locator('#stopTest').click();const returning=[];
 for(let i=0;i<20;i++){returning.push((await page.evaluate(()=>window.petDiagnostics.orientation))[1]);await page.waitForTimeout(20);}
 assert.ok(new Set(returning.map(v=>v.toFixed(3))).size>=3);
 assert.ok(Math.abs(returning.at(-1)-yaw)<.01);
 assert.ok(Math.abs((await page.evaluate(()=>window.petDiagnostics.orientation))[0]-.3)<.001,'Restore the saved vertical viewing angle');
 await panel.screenshot({path:'test-results/regression-010-panel.png'});
 writeFileSync('test-results/regression-010.json',JSON.stringify({scroll:{before,after},radius:4000,turn,returning,executable:process.env.BA_EXECUTABLE||'development'},null,2));
 console.log('Scroll preservation, wide radius, gradual turn and return passed');
}finally{await app.close();}
