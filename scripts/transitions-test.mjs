import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync,readFileSync,readdirSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const reportPath=process.env.BA_EXECUTABLE?'test-results/transitions-packaged.json':'test-results/transitions-ui.json';
const result=process.env.BA_RESUME?JSON.parse(readFileSync(reportPath,'utf8')):[];
const requested=process.argv.slice(2);
const characters=(requested.length?requested:readdirSync('characters',{withFileTypes:true}).filter(d=>d.isDirectory()).map(d=>d.name)).filter(c=>!process.env.BA_RESUME||!result.some(r=>r.character===c));
for(const character of characters){
 const folder=path.resolve('test-results/transitions',character);mkdirSync(folder,{recursive:true});
 writeFileSync(path.join(folder,'settings.json'),JSON.stringify({character,size:360,yaw:0,pitch:0,position:{x:400,y:180}}));
 const env={...process.env,BA_TEST_DATA:folder};delete env.ELECTRON_RUN_AS_NODE;
 const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:process.env.BA_EXECUTABLE,args:[]}:{args:['.']},env});
 try{
  const page=await app.firstWindow();await page.waitForFunction(()=>window.petDiagnostics?.frames>5);
  await app.evaluate(({screen})=>{globalThis.transitionCursor={x:-100000,y:-100000};screen.getCursorScreenPoint=()=>globalThis.transitionCursor;});
  async function moveMouse(x,y,options){
   await app.evaluate(({BrowserWindow},p)=>{const b=BrowserWindow.getAllWindows()[0].getBounds();globalThis.transitionCursor={x:b.x+p.x,y:b.y+p.y};},{x,y});
   await page.mouse.move(x,y,options);
  }
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.evaluate(()=>{
   window.samples=[];window.capture=false;let frame=-1;
   function sample(){
    const d=window.petDiagnostics;
    if(window.capture&&d.frames!==frame){
     frame=d.frames;window.samples.push({action:d.action,time:d.actionTime,transition:d.transition,
      image:document.querySelector('#pet').toDataURL()});
    }
    requestAnimationFrame(sample);
   }sample();
  });
  const stages=[];
  async function start(){await page.evaluate(()=>{window.samples=[];window.capture=true;});}
  async function check(stage,action){
   await page.waitForTimeout(350);
   await page.waitForFunction(action=>window.petDiagnostics.action===action&&window.petDiagnostics.transition.remaining===0,action,{timeout:3000});
   await page.waitForTimeout(40);
   const frames=await page.evaluate(()=>{window.capture=false;return window.samples;});
   const blending=frames.filter(f=>f.action===action&&f.transition.incoming>0.01&&f.transition.incoming<.99&&f.transition.outgoing>0.01);
   assert.ok(blending.length>=2,`${character}/${stage}: needs multiple blended frames, got ${blending.length}`);
   assert.equal(frames.at(-1).transition.remaining,0);
   if(character==='kisaki'||process.env.BA_CAPTURE_ALL)for(const [i,f]of frames.entries())writeFileSync(path.join(folder,`${stage}-${i}.png`),Buffer.from(f.image.split(',')[1],'base64'));
   stages.push({stage,frames:frames.map(({image,...d})=>d)});
  }
  let point;
  for(let y=140;y<=360&&!point;y+=20)for(let x=180;x<=360&&!point;x+=30){await moveMouse(x,y);await page.waitForTimeout(30);if(await page.evaluate(()=>window.petDiagnostics.hit))point={x,y};}
  assert.ok(point,'Character must be hittable');
  const manifest=JSON.parse(readFileSync(`characters/${character}/character.json`,'utf8'));
  if(manifest.actions?.some(a=>a.id==='pickup')){
   await page.mouse.down();await start();await moveMouse(point.x+15,point.y+10,{steps:2});await check('pickup','pickup');
   await page.waitForTimeout(700);await start();await page.mouse.up();await check('release','idle');
  }
  await app.evaluate(({Menu})=>{Menu.prototype.popup=function(o){globalThis.testMenu=this;o?.callback?.();};});
  await page.evaluate(()=>window.pet.menu());
  await app.evaluate(()=>globalThis.testMenu.getMenuItemById('action-interact').click());
  const duration=await page.evaluate(()=>window.petDiagnostics.durations.interact);
  await page.waitForTimeout(Math.max(0,(duration-.3)*1000));
  await start();await page.waitForFunction(()=>window.petDiagnostics.action==='idle',null,{timeout:5000});await check('natural-return','idle');
  assert.equal(await page.evaluate(()=>window.petDiagnostics.error),null);assert.deepEqual(errors,[]);
  result.push({character,stages,errors});console.log(character,'smooth pickup/release/natural return passed');
 }finally{await app.close();}
 writeFileSync(reportPath,JSON.stringify(result,null,2));
}
