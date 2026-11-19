// Inspect later original skill frames; their source clips deliberately hide the body at entry.
import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const executablePath=path.resolve(process.env.BA_EXECUTABLE);
const profile=path.resolve('test-results/wave9-skill-profile');mkdirSync(profile,{recursive:true});
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'hatsune_miku',size:360,eyeFollow:false,position:{x:450,y:180}}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({executablePath,args:[],env});const results=[];
try{
 const page=await app.firstWindow();await page.context().setOffline(true);
 await page.waitForFunction(()=>window.petDiagnostics?.frames>8);
 for(const action of ['original_exs','original_exs_cutin']){
  await app.evaluate(({BrowserWindow},id)=>BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html')).webContents.send('pet:action',id),action);
  await page.waitForFunction(id=>window.petDiagnostics.action===id,action);
  await page.evaluate(()=>{window.petDiagnostics.measurePose=true;});
  for(const time of (action==='original_exs'?[1.2,5,12,20]:[1.2,2,3])){
   await page.waitForFunction(t=>window.petDiagnostics.actionTime>=t,time,{timeout:30000});
   const d=await page.evaluate(()=>window.petDiagnostics);assert.equal(d.error,null);assert.equal(d.action,action);
   assert.ok(d.pose.size.every(Number.isFinite)&&d.pose.size[1]>0.1);
   await page.screenshot({path:`test-results/wave9-miku-${action}-${time}.png`,omitBackground:true});
   results.push({action,time,pose:d.pose,mouthTile:d.mouthTile});
  }
 }
 writeFileSync('test-results/wave9-skill-frames.json',JSON.stringify({executablePath,results},null,2));
 console.log('Miku later EX and Cutin frames have a visible finite body');
}finally{await app.close();}
