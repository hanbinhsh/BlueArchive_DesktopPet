import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync} from 'node:fs';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import path from 'node:path';
import assert from 'node:assert/strict';
const name=`local.bluearchive.desktoppet.validation-${Date.now()}`,profile=path.resolve(`test-results/${name}`),args=['--qol-startup-probe',name];
mkdirSync(profile,{recursive:true});writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'kisaki',allowOffscreen:true,position:{x:-6000,y:30}}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env}),child=app.process();
const report={complete:false,temporaryName:name,realLoginTested:false};
try{
 const page=await app.firstWindow();await page.waitForFunction(()=>window.petDiagnostics?.frames>2);
 report.states=await app.evaluate(({app},{name,args,moved})=>{
  app.setAppUserModelId(name);
  const original=process.execPath,states={},read=path=>{const s=app.getLoginItemSettings({path:`"${path}"`,args});return {registered:s.openAtLogin,enabled:s.openAtLogin&&!!s.launchItems.find(i=>i.name===name&&i.scope==='user')?.enabled};};
  const set=(path,registered,enabled)=>app.setLoginItemSettings({name,path,args,openAtLogin:registered,enabled});
  try{
   states.before=read(original);set(original,true,true);states.enabled=read(original);
   set(original,true,false);states.disabled=read(original);
   // Same temporary registration name, changed executable path, disabled preserved.
   set(moved,true,states.disabled.enabled);states.relocated=read(moved);states.oldPath=read(original);
   set(moved,false,false);states.removed=read(moved);return states;
  }finally{set(original,false,false);}
 },{name,args,moved:path.resolve('node_modules/electron/dist/electron.exe')});
 assert.deepEqual(report.states.before,{registered:false,enabled:false});
 assert.deepEqual(report.states.enabled,{registered:true,enabled:true});
 assert.deepEqual(report.states.disabled,{registered:true,enabled:false});
 assert.deepEqual(report.states.relocated,{registered:true,enabled:false});
 assert.deepEqual(report.states.oldPath,{registered:false,enabled:false});
 assert.deepEqual(report.states.removed,{registered:false,enabled:false});
 report.complete=true;
}finally{
 // Delete only this test's optional StartupApproved metadata, never daily entries.
 await promisify(execFile)('reg.exe',['delete','HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StartupApproved\\Run','/v',name,'/f']).catch(()=>{});
 writeFileSync('test-results/qol-release-startup.json',JSON.stringify(report,null,2));
 await app.evaluate(({app})=>app.exit(0)).catch(()=>{});child.kill();
}
console.log(report);process.exit(0);
