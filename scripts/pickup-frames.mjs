import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';
const tag=process.argv[2]||'fixed';
const folder=path.resolve('test-results/pickup-'+tag);mkdirSync(folder,{recursive:true});
writeFileSync(path.join(folder,'settings.json'),JSON.stringify({character:'kisaki',size:360,position:{x:400,y:180}}));
const env={...process.env,BA_TEST_DATA:folder};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({args:['.'],env});
try{
 const page=await app.firstWindow();await page.waitForFunction(()=>window.petDiagnostics?.frames>5);
 let point;for(let y=140;y<=360&&!point;y+=20)for(let x=180;x<=360&&!point;x+=30){await page.mouse.move(x,y);await page.waitForTimeout(30);if(await page.evaluate(()=>window.petDiagnostics.hit))point={x,y};}
 if(!point)throw new Error('No hit');
 await page.mouse.down();await page.mouse.move(point.x+15,point.y+10,{steps:3});
 if(process.argv.includes('--release')) { await page.waitForTimeout(1000); await page.mouse.up(); }
 const frames=[],start=Date.now();
 while(Date.now()-start<(process.argv.includes('--release')?2000:19000)){
  const d=await page.evaluate(()=>window.petDiagnostics);
  const name=String(frames.length).padStart(3,'0');
  await page.screenshot({path:path.join(folder,name+'.png'),omitBackground:true});
  frames.push({name,time:d.actionTime,action:d.action});await page.waitForTimeout(50);
 }
 await page.mouse.up();writeFileSync(path.join(folder,'frames.json'),JSON.stringify(frames));console.log(tag,frames.length);
}finally{await app.close();}
