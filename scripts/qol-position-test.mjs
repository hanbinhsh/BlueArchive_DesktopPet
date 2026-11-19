import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync,readFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const tag=process.env.BA_POSITION_TAG||'qol-position',profile=path.resolve(`test-results/${tag}-profile`);mkdirSync(profile,{recursive:true});const file=path.join(profile,'settings.json');
writeFileSync(file,JSON.stringify({character:'hina_pajamas',allowOffscreen:true,position:{x:-5000,y:-5000},size:280}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;const report=[];
for(const scenario of ['initial','restart','changed-layout','disabled']){
 if(scenario==='changed-layout'){const s=JSON.parse(readFileSync(file,'utf8'));s.displayLayout='test-layout-change';writeFileSync(file,JSON.stringify(s));}
 if(scenario==='disabled'){const s=JSON.parse(readFileSync(file,'utf8'));s.allowOffscreen=false;s.position={x:-5000,y:-5000};writeFileSync(file,JSON.stringify(s));}
 const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env});
 const child=app.process();
 try{const pet=await app.firstWindow();await pet.waitForFunction(()=>window.petDiagnostics?.frames>3);await pet.waitForTimeout(500);const actual=await app.evaluate(({BrowserWindow,screen})=>({bounds:BrowserWindow.getAllWindows()[0].getBounds(),displays:screen.getAllDisplays().map(d=>({bounds:d.workArea,scale:d.scaleFactor}))}));
  if(scenario==='initial'||scenario==='restart')assert.equal(actual.bounds.x,-5000);else assert.ok(actual.displays.some(({bounds:a})=>actual.bounds.x>=a.x&&actual.bounds.x+actual.bounds.width<=a.x+a.width+1));report.push({scenario,...actual});
 }finally{await app.evaluate(({app})=>app.exit(0)).catch(()=>{});child.kill();}
}
writeFileSync(`test-results/${tag}.json`,JSON.stringify({complete:true,report},null,2));console.log('Offscreen persistence across real restart, layout recovery and disabled clamp passed');

process.exit(0);
