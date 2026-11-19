import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import {transformSync} from 'esbuild';
const code=transformSync(readFileSync('src/startup.ts','utf8'),{loader:'ts',format:'cjs'}).code;
const current='C:\\Portable Apps\\BA Desktop Pet.exe',old='D:\\Old Pet\\BA Desktop Pet.exe',name='local.bluearchive.desktoppet';
function fixture(options:{testing?:boolean,packaged?:boolean,registered?:boolean,enabled?:boolean}={}){
 const writes:any[]=[],reads:any[]=[];
 let registered=options.registered??true,enabled=options.enabled??true;
 const app={isPackaged:options.packaged??true,getLoginItemSettings:(value:any)=>{reads.push(value);return {openAtLogin:registered,executableWillLaunchAtLogin:true,launchItems:[{name,scope:'user',enabled},{name:'another-entry',scope:'user',enabled:true}]};},setLoginItemSettings:(value:any)=>{writes.push(value);registered=value.openAtLogin;enabled=value.enabled;}};
 const module={exports:{} as any};runInNewContext(code,{module,require:()=>({app}),process:{execPath:current,env:options.testing?{BA_TEST_DATA:'isolated'}:{}}});
 return {api:module.exports,writes,reads};
}
test('startup lookup quotes paths and reads this registration, not another enabled entry',()=>{
 const f=fixture({enabled:false}),s=f.api.startupStatus();assert.equal(s.registered,true);assert.equal(s.enabled,false);assert.equal(f.reads[0].path,`"${current}"`);
});
test('test and development instances cannot change login items',()=>{
 for(const options of [{testing:true},{packaged:false}]){const f=fixture(options);assert.equal(f.api.startupStatus().available,false);assert.throws(()=>f.api.setStartup(true,{}));f.api.relocateStartup({startupEnabled:true,startupPath:old});assert.equal(f.writes.length,0);assert.equal(f.reads.length,0);}
});
test('portable relocation preserves an OS-disabled registration',()=>{
 const f=fixture({enabled:false}),s={startupEnabled:true,startupPath:old};f.api.relocateStartup(s);assert.equal(f.reads[0].path,`"${old}"`);assert.equal(f.writes[0].path,current);assert.equal(f.writes[0].enabled,false);assert.equal(s.startupPath,current);
});
test('externally removed login registration is not recreated',()=>{
 const f=fixture({registered:false}),s={startupEnabled:true,startupPath:old};f.api.relocateStartup(s);assert.equal(s.startupEnabled,false);assert.equal(f.writes.length,0);
});
test('startup toggles read back state and remember or clear the portable path',()=>{
 const f=fixture(),s:any={};assert.equal(f.api.setStartup(true,s).enabled,true);assert.equal(s.startupPath,current);assert.equal(f.api.setStartup(false,s).registered,false);assert.equal(s.startupEnabled,false);assert.equal(s.startupPath,'');assert.equal(f.writes[0].name,name);
});
