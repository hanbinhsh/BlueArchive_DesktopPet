import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync,readFileSync,existsSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const report=[];
for(const scenario of ['destroyed-pet','pending-range','cancel-dirty-quit']){
 const profile=path.resolve(`test-results/qol-close-${scenario}-${process.pid}`);mkdirSync(profile,{recursive:true});writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'kisaki'}));const errors=path.join(profile,'errors.log');writeFileSync(errors,'');
 const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
 const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env});
 const child=app.process();try{
  await app.evaluate(async({dialog},file)=>{const fs=process.getBuiltinModule('fs');process.on('uncaughtException',e=>fs.appendFileSync(file,String(e.stack)+'\n'));dialog.showErrorBox=(title,message)=>fs.appendFileSync(file,title+message+'\n');globalThis.quitAnswer=0;globalThis.quitQuestions=0;dialog.showMessageBoxSync=()=>{globalThis.quitQuestions++;return globalThis.quitAnswer;};},errors);
  const pet=await app.firstWindow();await pet.waitForFunction(()=>window.petDiagnostics?.frames>3);
  if(scenario!=='destroyed-pet'){
   await app.evaluate(({Menu})=>Menu.prototype.popup=function(){globalThis.closeMenu=this;});await pet.evaluate(()=>window.pet.menu());const p=app.waitForEvent('window');await app.evaluate(()=>globalThis.closeMenu.getMenuItemById('open-panel').click());const panel=await p;await panel.waitForSelector('[data-character]');
   if(scenario==='pending-range')await panel.evaluate(()=>window.panel.command('range-open'));
   else{await panel.locator('[data-page="combinations"]').click();await panel.locator('#addEntry').click();await pet.waitForTimeout(100);await app.evaluate(({app})=>app.quit());await pet.waitForTimeout(500);assert.equal(await app.evaluate(()=>globalThis.quitQuestions),1);const frames=await pet.evaluate(()=>window.petDiagnostics.frames);await pet.waitForTimeout(350);assert.ok(await pet.evaluate(n=>window.petDiagnostics.frames>n+2,frames));await app.evaluate(()=>globalThis.quitAnswer=1);}
  }
  const closed=app.waitForEvent('close',{timeout:6000});
  if(scenario==='destroyed-pet')await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('index.html')).destroy()).catch(()=>{});
  else await app.evaluate(({app})=>app.quit()).catch(()=>{});
  await closed;assert.equal(readFileSync(errors,'utf8'),'');report.push({scenario,passed:true});
 }finally{child.kill();}
}
writeFileSync('test-results/qol-close.json',JSON.stringify({complete:true,report},null,2));console.log(report);process.exit(0);
