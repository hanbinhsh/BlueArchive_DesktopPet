import {_electron as electron} from 'playwright';
import {mkdirSync,writeFileSync,readFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const profile=path.resolve('test-results/wave10-library-profile');mkdirSync(profile,{recursive:true});writeFileSync(path.join(profile,'settings.json'),JSON.stringify({character:'hina_pajamas',favorites:['hina_pajamas:interact'],size:280}));
const env={...process.env,BA_TEST_DATA:profile};delete env.ELECTRON_RUN_AS_NODE;
const launch=()=>electron.launch({...process.env.BA_EXECUTABLE?{executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]}:{args:['.']},env});
const report={complete:false,executable:process.env.BA_EXECUTABLE||'development',checks:[],errors:[]};let app=await launch(),child=app.process();
try{
 const pet=await app.firstWindow();await pet.waitForFunction(()=>window.petDiagnostics?.frames>3);
 await app.evaluate(({Menu,screen})=>{Menu.prototype.popup=function(){globalThis.libraryMenu=this;};screen.getCursorScreenPoint=()=>({x:-10000,y:-10000});});await pet.evaluate(()=>window.pet.menu());const opening=app.waitForEvent('window');await app.evaluate(()=>globalThis.libraryMenu.getMenuItemById('open-panel').click());const panel=await opening;panel.on('pageerror',e=>report.errors.push(e.message));await panel.waitForSelector('[data-character]');
 const initial=await panel.evaluate(()=>window.panel.state());
 await panel.locator('[data-character-favorite="hina"]').click();await panel.waitForFunction(()=>document.querySelector('#favoriteCharacters').textContent.includes('1'));
 await panel.locator('#favoriteCharacters').click();const expected=initial.characters.filter(c=>c.name.split(/[·（(]/)[0].trim()==='日奈').map(c=>c.id).sort();
 assert.deepEqual((await panel.locator('[data-character]').evaluateAll(es=>es.map(e=>e.dataset.character))).sort(),expected);report.checks.push('favorite character includes every outfit');
 await panel.locator('[data-character-favorite="hina"]').click();await panel.waitForFunction(()=>document.querySelectorAll('[data-character]').length===0);assert.ok(await panel.locator('#roster').textContent().then(t=>t.includes('收藏夹')));await panel.locator('#allCharacters').click();await panel.locator('[data-character-favorite="hina"]').click();await panel.waitForFunction(()=>document.querySelector('#favoriteCharacters').textContent.includes('1'));await panel.locator('#favoriteCharacters').click();report.checks.push('remove from favorites and recover from empty collection');
 await panel.locator('#search').fill('睡衣');assert.deepEqual(await panel.locator('[data-character]').evaluateAll(es=>es.map(e=>e.dataset.character)),['hina_pajamas']);await panel.locator('#search').fill('');
 const ids=()=>panel.locator('[data-action]').evaluateAll(es=>es.map(e=>e.dataset.action));assert.equal((await ids())[0],'interact');
 await panel.locator('#actionSort').selectOption('source');await panel.waitForFunction(()=>document.querySelector('#actionSort').value==='source');await panel.waitForTimeout(150);assert.deepEqual(await ids(),['interact',...initial.character.actions.filter(a=>a.id!=='interact').map(a=>a.id)]);
 await panel.locator('#actionSort').selectOption('name');await panel.waitForTimeout(150);const sorted=[...initial.character.actions.filter(a=>a.id!=='interact')].sort((a,b)=>new Intl.Collator('zh-CN',{numeric:true,sensitivity:'base'}).compare(a.label,b.label));assert.deepEqual(await ids(),['interact',...sorted.map(a=>a.id)]);report.checks.push('sort modes preserve favorite pin and original ordering');
 await panel.locator('[data-action="interact"]').click();await panel.waitForTimeout(200);assert.equal(await panel.locator('[data-character]').count(),expected.length);assert.equal(await panel.locator('#actionSort').inputValue(),'name');
 await panel.screenshot({path:'test-results/wave10-library.png'});
 await app.close();child.kill();const saved=JSON.parse(readFileSync(path.join(profile,'settings.json'),'utf8'));assert.deepEqual(saved.favoriteCharacters,['日奈']);assert.equal(saved.actionSort,'name');assert.deepEqual(saved.favorites,['hina_pajamas:interact']);report.checks.push('save independent character/action favorites and sort');
 app=await launch();child=app.process();const restored=await app.firstWindow();await restored.waitForFunction(()=>window.petDiagnostics?.frames>3);const state=await restored.evaluate(()=>window.pet.init());assert.deepEqual(state.settings.favoriteCharacters,['日奈']);assert.equal(state.settings.actionSort,'name');report.checks.push('restart restores library preferences');
 assert.deepEqual(report.errors,[]);report.complete=true;
}finally{writeFileSync('test-results/wave10-library.json',JSON.stringify(report,null,2));await app.evaluate(({app})=>app.exit(0)).catch(()=>{});child.kill();}
console.log(report);process.exit(0);
