import {_electron as electron} from 'playwright';

import {mkdirSync,writeFileSync,readFileSync} from 'node:fs';

import path from 'node:path';

import assert from 'node:assert/strict';

const executablePath=process.env.BA_EXECUTABLE;assert.ok(executablePath);

const added=Object.keys(JSON.parse(readFileSync('.assets/wave8-all-specs.json','utf8')));

const profile=path.resolve('test-results/wave8-panel-profile');mkdirSync(profile,{recursive:true});

writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'yuuka',size:360,position:{x:450,y:180}}));

const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;

const app=await electron.launch({executablePath,args:[],env});const results=[],errors=[];

try{

 const page=await app.firstWindow();page.on('pageerror',e=>errors.push(e.message));

 await page.waitForFunction(()=>window.petDiagnostics?.frames>5);await app.context().setOffline(true);

 await app.evaluate(({Menu,screen})=>{Menu.prototype.popup=function(options){globalThis.testMenu=this;options?.callback?.();};screen.getCursorScreenPoint=()=>({x:-100000,y:-100000});});

 await page.evaluate(()=>window.pet.menu());await page.waitForTimeout(80);const event=app.waitForEvent('window');

 await app.evaluate(()=>globalThis.testMenu.getMenuItemById('open-panel').click());

 const panel=await event;panel.on('pageerror',e=>errors.push(e.message));

 await panel.waitForFunction(()=>document.querySelectorAll('.card img').length===100&&[...document.querySelectorAll('.card img')].every(i=>i.complete&&i.naturalWidth>0));

 for(const character of added){

  const manifest=JSON.parse(readFileSync(`characters/${character}/character.json`,'utf8'));

  const card=panel.locator(`[data-character="${character}"]`);await card.scrollIntoViewIfNeeded();const before=await panel.evaluate(()=>scrollY);

  if(character!=='yuuka'){const loaded=page.waitForEvent('load');await card.click();await loaded;await page.waitForFunction(()=>window.petDiagnostics?.frames>5);}

  await panel.waitForFunction(id=>document.querySelector(`[data-character="${id}"]`).getAttribute('aria-pressed')==='true'&&!document.querySelector('[data-action="idle"]').disabled,character);

  const after=await panel.evaluate(()=>scrollY);assert.ok(Math.abs(after-before)<=2);

  assert.equal(await panel.locator('#characterNote').textContent(),manifest.note||'');

  assert.deepEqual((await panel.locator('[data-action]').evaluateAll(ns=>ns.map(n=>n.dataset.action))).sort(),manifest.actions.map(a=>a.id).sort());

  await panel.locator('[data-action="interact"]').click();await page.waitForFunction(()=>window.petDiagnostics.action==='interact');

  await panel.locator('[data-action="idle"]').click();await page.waitForFunction(()=>window.petDiagnostics.action==='idle');

  await panel.locator('#actionCategory').selectOption('常用');

  assert.equal(await panel.locator('[data-action]').count(),manifest.actions.filter(a=>(a.category||'常用')==='常用').length);

  await panel.locator('#actionCategory').selectOption('');

  const extra=manifest.actions.find(a=>a.sourceName);

  if(extra){await panel.locator('#actionSearch').fill(extra.sourceName);assert.ok(await panel.locator(`[data-action="${extra.id}"]`).count());await panel.locator('#actionSearch').fill('');}

  await panel.locator('[data-favorite="interact"]').click();await panel.locator('#onlyFavorites').check();

  await panel.waitForFunction(()=>document.querySelectorAll('[data-action]').length===1);

  assert.equal(await panel.locator('[data-action]').getAttribute('data-action'),'interact');

  await panel.locator('#onlyFavorites').uncheck();

  await panel.locator('[data-favorite="interact"]').click();

  results.push({character,scrollBefore:before,scrollAfter:after,note:true,actionList:true,categories:true,sourceSearch:true,favorites:true});

 }

 await panel.screenshot({path:'test-results/wave8-panel.png'});assert.deepEqual(errors,[]);

 writeFileSync('test-results/wave8-panel.json',JSON.stringify({executable:executablePath,offline:true,thumbnails:100,results,errors},null,2));

 console.log('100 thumbnails and 16 character/action lists passed; scroll retained');

}finally{await app.close();}

