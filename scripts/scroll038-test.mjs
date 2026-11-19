import {openTestPanel} from './themed-menu-test-helper.mjs';
import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const tag=process.env.BA_SCROLL_TAG||'panel-action-scroll';
const profile=path.resolve(`test-results/${tag}-profile`);mkdirSync(profile,{recursive:true});
writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'otogi',size:280,position:{x:450,y:180},favorites:[]}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env});
const results=[],errors=[];
const report={executable:process.env.BA_EXECUTABLE||'development',results,errors,complete:false};
try{
 const pet=await app.firstWindow();await pet.waitForFunction(()=>window.petDiagnostics?.frames>5);
 await app.context().setOffline(true);
 await app.evaluate(({screen})=>{screen.getCursorScreenPoint=()=>({x:-100000,y:-100000});});
 const panel=await openTestPanel(app,pet);panel.on('pageerror',e=>errors.push(e.message));
 await panel.waitForFunction(()=>document.querySelectorAll('[data-action]').length===50&&!document.querySelector('[data-action]').disabled);
 const position=()=>panel.evaluate(()=>({aside:document.querySelector('aside').scrollTop,page:document.querySelector('#wardrobe')?.scrollTop??scrollY}));
 async function check(label,button){
  await button.scrollIntoViewIfNeeded();await panel.waitForTimeout(100);
  const before=await position();await button.click();await panel.waitForTimeout(500);const after=await position();
  results.push({label,before,after});
  assert.ok(Math.abs(before.aside-after.aside)<=2,`${label}: action panel jumped from ${before.aside} to ${after.aside}`);
  assert.ok(Math.abs(before.page-after.page)<=2,`${label}: page moved`);
 }
 const deep=panel.locator('[data-action]').nth(35);const id=await deep.getAttribute('data-action');
 await check('play lower action',deep);await pet.waitForFunction(id=>window.petDiagnostics.action===id,id);
 await check('repeat lower action',panel.locator(`[data-action="${id}"]`));
 await check('favorite lower action',panel.locator(`[data-favorite="${id}"]`));
 await panel.locator('[data-page="automatic"]').click();await check('change auto setting',panel.locator('#eyeFollow'));await panel.locator('[data-page="characters"]').click();
 await panel.locator('#actionCategory').selectOption('战斗');
 const count=await panel.locator('[data-action]').count();assert.ok(count>5);
 await check('play filtered action',panel.locator('[data-action]').last());
 await panel.locator('#actionCategory').selectOption('');
 await panel.locator('#actionSearch').fill('CH0174');
 assert.ok(await panel.locator('[data-action]').count()>5);
 await check('play search result',panel.locator('[data-action]').last());
 await panel.locator('#actionSearch').fill('');await panel.locator('#onlyFavorites').check();
 assert.equal(await panel.locator('[data-action]').count(),1);
 await check('play favorite only',panel.locator('[data-action]'));
 await panel.locator('#onlyFavorites').uncheck();
 const card=panel.locator('[data-character="moe_swimsuit"]');await card.scrollIntoViewIfNeeded();
 const before=await position();await card.click();await panel.waitForFunction(()=>document.querySelector('[data-character="moe_swimsuit"]').getAttribute('aria-pressed')==='true'&&!document.querySelector('[data-action]').disabled);
 assert.ok(Math.abs((await position()).page-before.page)<=2,'character selection keeps page position');
 await check('play after character switch',panel.locator('[data-action]').last());
 assert.deepEqual(errors,[]);await panel.screenshot({path:`test-results/${tag}.png`});report.complete=true;
 console.log('Action clicks, repeated play, favorites, settings, filters and character switch retain scroll');
}finally{writeFileSync(`test-results/${tag}.json`,JSON.stringify(report,null,2));await app.close();}
