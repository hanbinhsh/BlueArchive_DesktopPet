import {_electron as electron} from 'playwright';
import path from 'node:path';
import {writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const env={...process.env};delete env.BA_TEST_DATA;delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({args:['.'],env}),child=app.process();
try{
 const page=await app.firstWindow();await page.waitForFunction(()=>window.petDiagnostics?.frames>2);
 const profile=await app.evaluate(({app})=>app.getPath('userData'));
 assert.equal(profile,path.resolve('.dev-profile'));
 writeFileSync('test-results/qol-dev-profile.json',JSON.stringify({complete:true,profile},null,2));
}finally{await app.evaluate(({app})=>app.exit(0)).catch(()=>{});child.kill();}
process.exit(0);
