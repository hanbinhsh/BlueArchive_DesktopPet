import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const profile=path.resolve('test-results/view-profile');mkdirSync(profile,{recursive:true});
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'serika',size:360,yaw:0,pitch:0,position:{x:450,y:180}}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const launch=()=>electron.launch({...process.env.BA_EXECUTABLE?{executablePath:process.env.BA_EXECUTABLE,args:[]}:{args:['.']},env});
let app=await launch();
try {
 let p=await app.firstWindow();await p.waitForFunction(()=>window.petDiagnostics?.frames>5);
 await app.evaluate(({Menu})=>{Menu.prototype.popup=function(){globalThis.viewMenu=this;};});
 const select=async id=>{await p.evaluate(()=>window.pet.menu());await app.evaluate(({BrowserWindow},id)=>{const m=globalThis.viewMenu.getMenuItemById(id);m.click(m,BrowserWindow.getAllWindows()[0],{});},id);};
 await select('view-down');await p.waitForTimeout(300);
 assert.ok(Math.abs((await p.evaluate(()=>window.pet.init())).settings.pitch-Math.PI/12)<1e-6);
 await p.screenshot({path:'test-results/view-down.png',omitBackground:true});
 await select('view-reset');await p.waitForTimeout(100);
 let point;
 for(let y=140;y<=330&&!point;y+=20)for(let x=180;x<=360&&!point;x+=30){await p.mouse.move(x,y);await p.waitForTimeout(30);if(await p.evaluate(()=>window.petDiagnostics.hit))point={x,y};}
 assert.ok(point);await p.keyboard.down('Control');await p.mouse.down();await p.mouse.move(point.x,point.y+45,{steps:5});await p.mouse.up();await p.keyboard.up('Control');
 await p.waitForTimeout(400);const setting=(await p.evaluate(()=>window.pet.init())).settings;
 assert.ok(setting.pitch>.2);assert.equal(setting.yaw,0);assert.equal(await p.evaluate(()=>window.petDiagnostics.action),'idle');
 await p.screenshot({path:'test-results/view-ctrl-drag.png',omitBackground:true});
 await app.close();app=await launch();p=await app.firstWindow();await p.waitForFunction(()=>window.petDiagnostics?.frames>5);
 assert.equal((await p.evaluate(()=>window.pet.init())).settings.pitch,setting.pitch);
 writeFileSync('test-results/view.json',JSON.stringify({menu:true,ctrlDrag:true,restart:true,pitch:setting.pitch},null,2));console.log('Vertical rotation: menu, Ctrl drag, restart passed');
}finally{await app.close();}
