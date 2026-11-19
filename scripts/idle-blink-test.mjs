import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync,readFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const profile=path.resolve('test-results/idle-blink-profile');mkdirSync(profile,{recursive:true});
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'plana',size:420,yaw:0,position:{x:450,y:150}}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:process.env.BA_EXECUTABLE,args:[]}:{args:['.']},env});
try{
 const page=await app.firstWindow();await page.waitForFunction(()=>window.petDiagnostics?.frames>5);
 await page.evaluate(()=>window.petDiagnostics.measureFace=true);
 const bytes=readFileSync('characters/plana/model.glb');const doc=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)));
 const closed='visible-'+doc.nodes.findIndex(n=>n.name==='Plana_Original_FaceEmo02' && 'mesh' in n);
 await page.waitForFunction(()=>window.petDiagnostics.action==='blink',null,{timeout:10000});
 await page.waitForFunction(key=>window.petDiagnostics.face?.[key]?.[0]===1,closed,{timeout:5000,polling:10});
 const at=await page.evaluate(()=>({action:window.petDiagnostics.action,time:window.petDiagnostics.actionTime}));
 assert.equal(at.action,'blink');
 await page.screenshot({path:'test-results/idle-blink-closed.png',omitBackground:true});
 await page.waitForFunction(()=>window.petDiagnostics.action==='idle');
 await page.waitForFunction(key=>window.petDiagnostics.face[key][0]===0,closed);
 assert.equal(await page.evaluate(()=>window.petDiagnostics.error),null);
 writeFileSync('test-results/idle-blink.json',JSON.stringify({automatic:true,closedFace:true,restored:true,at,executable:process.env.BA_EXECUTABLE||'development'},null,2));
 console.log('Original idle blink, closed face, return to idle passed');
}finally{await app.close();}
