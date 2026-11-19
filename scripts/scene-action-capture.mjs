import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const tag=process.env.BA_SCENE_TAG||'scene-audit-before',results=[];
const profile=path.resolve(`test-results/${tag}-profile`);mkdirSync(profile,{recursive:true});
for(const character of process.argv.slice(2).length?process.argv.slice(2):['natsu_band_relax','hina_pajamas']){
 writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character,size:360,yaw:0,position:{x:400,y:160}}));
 const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
 const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:process.env.BA_EXECUTABLE,args:[]}:{args:['.']},env});
 try{
  const page=await app.firstWindow();await page.waitForFunction(()=>window.petDiagnostics?.frames>5);await page.context().setOffline(true);
  const init=await page.evaluate(()=>window.pet.init());
  for(const a of init.character.actions.filter(a=>character==='natsu_band_relax'||/bed_day00|windowsofa_01_ing/.test(a.id))){
   await app.evaluate(({BrowserWindow},id)=>BrowserWindow.getAllWindows()[0].webContents.send('pet:action',id),a.id);
   await page.waitForFunction(id=>window.petDiagnostics.action===id,a.id);
   await page.evaluate(()=>window.petDiagnostics.measurePose=true);
   const duration=await page.evaluate(id=>window.petDiagnostics.durations[id],a.id),samples=[];
   for(const fraction of [.05,.25,.5,.75,.94]){
    await page.waitForFunction(({id,time})=>window.petDiagnostics.action!==id||window.petDiagnostics.actionTime>=time,{id:a.id,time:duration*fraction},{timeout:60000});
    const d=await page.evaluate(()=>window.petDiagnostics);assert.equal(d.error,null);assert.equal(d.action,a.id);
    await page.screenshot({path:`test-results/${tag}-${character}-${a.id}-${fraction}.png`,omitBackground:true});
    samples.push({fraction,time:d.actionTime,pose:d.pose,mouthTile:d.mouthTile});
   }
   results.push({character,action:a.id,duration,samples});console.log(character,a.id,duration,'captured');
   writeFileSync(`test-results/${tag}.json`,JSON.stringify(results,null,2));
  }
 }finally{await app.close();}
}
