import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const profile=path.resolve('test-results/qol-displays-profile');mkdirSync(profile,{recursive:true});writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'kisaki',position:{x:100,y:100},size:280}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env});const report={complete:false,screens:[],samples:[]};
const child=app.process();
try{
 const pet=await app.firstWindow();await pet.waitForFunction(()=>window.petDiagnostics?.frames>5);await app.evaluate(({screen})=>screen.getCursorScreenPoint=()=>({x:-10000,y:-10000}));
 report.screens=await app.evaluate(({screen})=>screen.getAllDisplays().map(d=>({id:d.id,area:d.workArea,scale:d.scaleFactor})));
 for(const d of [...report.screens,...report.screens.toReversed()]){
  await app.evaluate(({BrowserWindow},d)=>BrowserWindow.getAllWindows()[0].setPosition(d.area.x+100,d.area.y+100),d);await pet.evaluate(()=>window.pet.drag(false));await pet.waitForTimeout(600);
  for(const size of [400,280]){await pet.evaluate(s=>window.pet.resize(s),size);await pet.waitForTimeout(300);const sample=await pet.evaluate(()=>({dpr:devicePixelRatio,client:[innerWidth,innerHeight],canvas:[document.querySelector('canvas').width,document.querySelector('canvas').height],error:window.petDiagnostics.error}));sample.bounds=await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows()[0].getBounds());sample.display=d.id;sample.size=size;
   assert.equal(sample.error,null);assert.ok(Math.abs(sample.dpr-d.scale)<.01);assert.ok(Math.abs(sample.bounds.width-size*1.5)<=2);assert.ok(Math.abs(sample.bounds.height-size*1.45)<=2);assert.ok(Math.abs(sample.canvas[0]-Math.round(size*1.5)*d.scale)<=1);report.samples.push(sample);
  }
 }
 if(report.screens.length>1){await app.evaluate(({BrowserWindow,screen})=>{const first=screen.getAllDisplays()[0],last=screen.getAllDisplays().at(-1);BrowserWindow.getAllWindows()[0].setPosition(last.workArea.x+100,last.workArea.y+100);globalThis.originalDisplays=screen.getAllDisplays;screen.getAllDisplays=()=>[first];screen.emit('display-removed',{},last);});await pet.waitForTimeout(300);const b=await app.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows()[0].getBounds()),a=report.screens[0].area;assert.ok(b.x>=a.x&&b.x+b.width<=a.x+a.width+1);report.simulatedDisconnectRecovered=true;}
 report.complete=true;
}finally{writeFileSync('test-results/qol-packaged-displays.json',JSON.stringify(report,null,2));await app.evaluate(({app})=>app.exit(0)).catch(()=>{});child.kill();}
console.log('Physical displays / mixed DPI / resize verified; disconnect event simulated');process.exit(0);
