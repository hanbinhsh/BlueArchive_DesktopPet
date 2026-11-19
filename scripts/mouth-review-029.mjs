import {openTestPanel} from './themed-menu-test-helper.mjs';
import {_electron as electron} from 'playwright';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(process.env.BA_CHARACTERS||'characters'),tag=process.env.BA_MOUTH_TAG||'mouth029',profile=path.resolve(`test-results/${tag}-profile`);
const ids=process.env.BA_MOUTH_IDS?.split(',')||['hina','hina_swimsuit','kayoko_dress','tsumugi','aru_dress'];
mkdirSync(profile,{recursive:true});writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:ids[0],position:{x:400,y:150},size:360,eyeFollow:false,outline:true,outlineWidth:38}));
const env={...process.env,BA_TEST_DATA:profile,BA_CHARACTERS:root};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env}),results=[],errors=[];
try{
 const page=await app.firstWindow();page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.waitForFunction(()=>window.petDiagnostics?.frames>5&&!window.petDiagnostics.loading);
 await app.context().setOffline(true);await app.evaluate(({screen})=>{screen.getCursorScreenPoint=()=>({x:-10000,y:-10000});});
 const panel=await openTestPanel(app,page);
 for(const [index,id] of ids.entries()){
  if(index){const loaded=page.waitForEvent('load');await panel.evaluate(id=>window.panel.command('select',id),id);await loaded;}
  await page.waitForFunction(()=>window.petDiagnostics?.frames>5&&!window.petDiagnostics.loading);
  const c=JSON.parse(readFileSync(path.join(root,id,'character.json'))),m=c.mouth;
  for(const action of ['idle','interact','pickup'].filter(id=>c.actions.some(a=>a.id===id))){
   await page.evaluate(()=>{delete window.petDiagnostics.freezeTime;});
   await panel.evaluate(id=>window.panel.command('action',id),action);
   await page.waitForFunction(id=>window.petDiagnostics?.sceneAction===id,action);
   const clip=c.actions.find(a=>a.id===action).clip;
   for(const time of [0,.4,1]){
    await page.evaluate(time=>{window.petDiagnostics.freezeTime=time;},time);await page.waitForTimeout(120);
    const d=await page.evaluate(()=>window.petDiagnostics);assert.equal(d.error,null);
    if(m){
     const e=(m.events[clip]||[]).filter(e=>e.time<=time).at(-1),tile=e?.tile??m.defaultTile,flip=e?.flipped===true,cols=m.columns??8,rows=m.rows??8;
     const base=m.baseUV||[m.defaultTile%100/cols,Math.floor(m.defaultTile/100)/rows];
     const offset=m.baseUV&&(!e||e.reset)?[0,0]:[flip?(tile%100+1)/cols+base[0]:tile%100/cols-base[0],base[1]-Math.floor(tile/100)/rows];
     const actual=d.mouthMaps.find(x=>x.material===m.material).offset;assert.ok(actual.every((x,i)=>Math.abs(x-offset[i])<1e-6),`${id} ${action} ${time}: ${actual} != ${offset}`);
    }
    await page.screenshot({path:`test-results/${tag}-${id}-${action}-${time}.png`,omitBackground:true});
    results.push({character:id,action,time,mouthTile:d.mouthTile,mouthMaps:d.mouthMaps});
   }
  }
  if(id==='aru_dress'){
   await page.evaluate(()=>{delete window.petDiagnostics.freezeTime;});await panel.evaluate(()=>window.panel.command('furniture','f210333_1'));
   await page.waitForFunction(()=>window.petDiagnostics?.sceneAction==='f210333_1'&&!window.petDiagnostics.loading);
   await page.evaluate(()=>{window.petDiagnostics.freezeTime=2;});await page.waitForTimeout(150);
   const d=await page.evaluate(()=>window.petDiagnostics);assert.equal(new Set(d.mouthMaps.map(m=>m.texture)).size,d.mouthMaps.length);
   await page.screenshot({path:`test-results/${tag}-aru-kayoko-duo.png`,omitBackground:true});
  }
  console.log('PASS',id);
 }
 assert.deepEqual(errors,[]);
}finally{writeFileSync(`test-results/${tag}.json`,JSON.stringify({results,errors},null,2));await app.close();}
