import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync,readFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const source=JSON.parse(readFileSync('test-results/expression-source.json'));
const results=[];
for(const entry of source.filter(x=>process.argv.length<=2||process.argv.slice(2).includes(x.character))){
 const profile=path.resolve('test-results/expressions-profile');mkdirSync(profile,{recursive:true});
 writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:entry.character,size:420,yaw:0,position:{x:400,y:150}}));
 const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
 const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env});
 try{
  const page=await app.firstWindow();await page.waitForFunction(()=>window.petDiagnostics?.frames>5);
  const init=await page.evaluate(()=>window.pet.init());
  const checked=[];
  for(const id of entry.character==='plana'?['idle','interact','blink','blink2','smile']:['idle','interact']){
   await app.evaluate(({BrowserWindow},id)=>BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html')).webContents.send('pet:action',id),id);
   await page.evaluate(()=>window.petDiagnostics.measureFace=true);
   await page.waitForTimeout(250);
   const baseline=await page.evaluate(()=>window.petDiagnostics.face);
   const changed=new Set();const duration=await page.evaluate(id=>window.petDiagnostics.durations[id],id);
   const start=Date.now();let shot=false;const mouths=new Set();
   while(Date.now()-start<duration*1000-250){
    await page.waitForTimeout(45);const d=await page.evaluate(()=>window.petDiagnostics);
    if(d.action!==id)break;
    for(const [name,values] of Object.entries(d.face))if(values.some((v,i)=>Math.abs(v-(baseline[name]?.[i]??v))>1e-4))changed.add(name);
    mouths.add(d.mouthTile);
    if(init.character.mouth){
     const mouth=init.character.mouth,clip=init.character.actions.find(a=>a.id===id).clip;
     const event=mouth.events[clip]?.filter(e=>e.time<=d.actionTime).at(-1);
     assert.equal(d.mouthTile,event?.tile??mouth.defaultTile);
     assert.equal(d.mouthFlipped,event?.flipped===true);
    }
    if(!shot&&changed.size){await page.screenshot({path:`test-results/expression-${entry.character}-${id}.png`,omitBackground:true});shot=true;}
   }
   const clip=init.character.actions.find(a=>a.id===id).clip;
   const original=entry.clips.find(c=>c.clip===clip);
   const brows=[...changed].filter(n=>/brow|blow/i.test(n));const eyes=[...changed].filter(n=>/eye/i.test(n));const visibility=[...changed].filter(n=>n.startsWith('visible-'));
   if(original.varyingSkinnedFaceBones.brows.length)assert.ok(brows.length,entry.character+' '+id+' eyebrows must move');
   if(original.varyingSkinnedFaceBones.eyes.length)assert.ok(eyes.length,entry.character+' '+id+' eye bones must move');
   checked.push({id,brows,eyes,visibility,mouthTiles:[...mouths]});
  }
  results.push({character:entry.character,checked});console.log(entry.character,'face tracks passed');
 }finally{await app.close();}
 writeFileSync('test-results/expressions.json',JSON.stringify(results,null,2));
}
