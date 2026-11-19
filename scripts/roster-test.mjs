import { _electron as electron } from 'playwright';
import { mkdirSync, writeFileSync, readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const profile = path.resolve('test-results/roster-profile');
mkdirSync(profile, { recursive: true });
const roster = readdirSync('characters', { withFileTypes: true }).filter(x => x.isDirectory()).map(x => x.name).filter(x => process.argv.length <= 2 || process.argv.slice(2).includes(x));
writeFileSync(path.join(profile,'settings.json'), JSON.stringify({character:roster[0],size:360,yaw:0,alwaysOnTop:true,position:{x:450,y:180}}));
const env = {...process.env, BA_TEST_DATA:profile}; delete env.ELECTRON_RUN_AS_NODE;
const launch = () => electron.launch({...process.env.BA_EXECUTABLE ? {executablePath:path.resolve(process.env.BA_EXECUTABLE),args:[]} : {args:['.']},env});
let app = await launch();
const results=[];
try {
  let page = await app.firstWindow();
  const errors=[]; page.on('pageerror', e => errors.push(e.message));
  await app.evaluate(({Menu}) => {Menu.prototype.popup=function(){globalThis.rosterMenu=this;};});
  await app.evaluate(({screen})=>{
    globalThis.rosterCursor={x:-100000,y:-100000};screen.getCursorScreenPoint=()=>globalThis.rosterCursor;
  });
  async function moveMouse(x,y,options){
    await app.evaluate(({BrowserWindow},p)=>{const b=BrowserWindow.getAllWindows()[0].getBounds();globalThis.rosterCursor={x:b.x+p.x,y:b.y+p.y};},{x,y});
    await page.mouse.move(x,y,options);
  }
  async function select(id) {
    await page.evaluate(() => window.pet.menu());
    await app.evaluate(({BrowserWindow},id) => {
      const item=globalThis.rosterMenu.getMenuItemById(id);
      if(!item)throw new Error('Missing menu '+id);
      item.click(item,BrowserWindow.getAllWindows()[0],{});
    },id);
  }
  for (const character of roster) {
    if (character !== roster[0]) { const loaded=page.waitForEvent('load'); await select('costume-'+character); await loaded; }
    await page.waitForFunction(() => window.petDiagnostics?.frames>5);
    await page.context().setOffline(true);
    const init=await page.evaluate(() => window.pet.init());
    assert.equal(init.character.id,character);
    assert.equal(await page.evaluate(()=>window.petDiagnostics.error),null);
    await page.screenshot({path:`test-results/verified-${character}-idle.png`,omitBackground:true});
    const actions=[];
    for(const action of init.character.actions.filter(a=>a.id!=='idle')) {
      await select('action-'+action.id);
      await page.waitForFunction(id=>window.petDiagnostics.action===id,action.id);
      await page.waitForTimeout(700);
      await page.screenshot({path:`test-results/verified-${character}-${action.id}.png`,omitBackground:true});
      await page.waitForFunction(()=>window.petDiagnostics.action==='idle',null,{timeout:30000});
      actions.push(action.id);
    }
    let hitPoint;
    for(let y=140;y<=360&&!hitPoint;y+=20) for(let x=180;x<=360&&!hitPoint;x+=30) {
      await moveMouse(x,y); await page.waitForTimeout(30);
      if(await page.evaluate(()=>window.petDiagnostics.hit))hitPoint={x,y};
    }
    assert.ok(hitPoint,'Character accepts pointer input');
    await page.mouse.down(); await moveMouse(hitPoint.x+15,hitPoint.y+10,{steps:3});
    await page.waitForTimeout(300);
    assert.equal(await page.evaluate(()=>window.petDiagnostics.action),init.character.actions.some(a=>a.id==='pickup')?'pickup':'idle');
    await page.mouse.up(); await page.waitForFunction(()=>window.petDiagnostics.action==='idle');
    await moveMouse(5,5); await page.waitForFunction(()=>!window.petDiagnostics.hit);
    results.push({character,actions,drag:true,transparentHitTest:true,offline:true});
    console.log(character+': passed');
  }
  assert.deepEqual(errors,[]);
  await page.waitForTimeout(300); await app.close();
  assert.equal(JSON.parse(readFileSync(path.join(profile,'settings.json'))).character,roster.at(-1));
  app=await launch();page=await app.firstWindow();await page.waitForFunction(()=>window.petDiagnostics?.frames>5);
  assert.equal((await page.evaluate(()=>window.pet.init())).character.id,roster.at(-1));
  writeFileSync('test-results/roster.json',JSON.stringify({results,restart:true,executable:process.env.BA_EXECUTABLE||'development'},null,2));
} finally {await app.close();}
