import {openTestPanel} from './themed-menu-test-helper.mjs';
import {_electron as electron} from 'playwright';
import {readFileSync,writeFileSync,readdirSync,mkdirSync,existsSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(process.env.BA_CHARACTERS||(process.env.BA_EXECUTABLE?path.join(path.dirname(process.env.BA_EXECUTABLE),'resources/characters'):'.assets/expanded-ready'));
const selected=process.argv.slice(2),ids=readdirSync(root).filter(id=>existsSync(path.join(root,id,'character.json'))&&(!selected.length||selected.includes(id)));
const profile=path.resolve('test-results/wave14-runtime-profile');mkdirSync(profile,{recursive:true});
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:ids[0],size:360,eyeFollow:false,allowOffscreen:true,position:{x:450,y:180}}));
const env={...process.env,BA_CHARACTERS:root,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const launch=()=>electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env});
let app=await launch();
const results=[],errors=[];
const reportPath=process.env.BA_RUNTIME_REPORT||'test-results/wave14-runtime.json';
try{
 const page=await app.firstWindow();page.on('pageerror',e=>errors.push(e.message));
 const panel=await openTestPanel(app,page);await app.evaluate(({BrowserWindow})=>{const w=BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html'));w.setFocusable(false);w.setBounds({...w.getBounds(),x:-4000,y:180});});
 await app.evaluate(({screen})=>{screen.getCursorScreenPoint=()=>({x:-100000,y:-100000});});
 await page.context().setOffline(true);
 for(const id of ids){
  if(id!==ids[0]){const load=page.waitForEvent('load');await panel.evaluate(id=>window.panel.command('select',id),id);await load;}
  await page.waitForFunction(()=>window.petDiagnostics?.frames>8||window.petDiagnostics?.error);
  assert.equal(await page.evaluate(()=>window.petDiagnostics.error),null,id);
  const init=await page.evaluate(()=>window.pet.init());assert.equal(init.character.id,id);
  assert.equal(init.character.actions.length,JSON.parse(readFileSync(path.join(root,id,'character.json'))).actions.length);
  const fresh=existsSync(`${process.env.BA_FRESH_ROOT||'.assets/wave14-ready'}/${id}/character.json`);
  if(fresh)await page.screenshot({path:`test-results/wave14-${id}-idle.png`,omitBackground:true});
  const samples=fresh?init.character.actions: [...new Map(init.character.actions.map(a=>[a.category||'常用',a])).values()];
  const tested=[];
  for(const a of samples.filter(a=>a.id!=='idle')){
   const frames=await page.evaluate(()=>window.petDiagnostics.frames);
   await app.evaluate(({BrowserWindow},action)=>BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html')).webContents.send('pet:action',action),a.id);
   await page.waitForTimeout(360);
   const d=await page.evaluate(()=>window.petDiagnostics);
   assert.equal(d.error,null,`${id}/${a.id}`);assert.ok(d.frames>frames,`${id}/${a.id}: renders`);
   assert.ok([a.id,'idle'].includes(d.action),`${id}/${a.id}: selected ${d.action}`);
   if(fresh&&['interact','pickup','original_formation_idle','original_exs'].includes(a.id))await page.screenshot({path:`test-results/wave14-${id}-${a.id}.png`,omitBackground:true});
   tested.push(a.id);
  }
  await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html')).webContents.send('pet:action','idle'));
  await page.waitForFunction(()=>window.petDiagnostics.action==='idle');await page.waitForTimeout(220);
  assert.equal(await page.evaluate(()=>window.petDiagnostics.error),null);
  results.push({character:id,available:init.character.actions.length,played:tested,offline:true,returnedToIdle:true});
  writeFileSync(reportPath,JSON.stringify({executable:process.env.BA_EXECUTABLE||'development',root,results,errors,complete:false},null,2));
  console.log(id,tested.length,'passed');
 }
 assert.deepEqual(errors,[]);
 await page.waitForTimeout(400);await app.close();
 assert.equal(JSON.parse(readFileSync(path.join(profile,'settings.json'))).character,ids.at(-1));
 app=await launch();const resumed=await app.firstWindow();await resumed.context().setOffline(true);
 await resumed.waitForFunction(()=>window.petDiagnostics?.frames>8||window.petDiagnostics?.error);
 assert.equal((await resumed.evaluate(()=>window.pet.init())).character.id,ids.at(-1));
 assert.equal(await resumed.evaluate(()=>window.petDiagnostics.error),null);
 writeFileSync(reportPath,JSON.stringify({executable:process.env.BA_EXECUTABLE||'development',root,results,errors,restart:true,complete:true},null,2));
}finally{await app.close();}
