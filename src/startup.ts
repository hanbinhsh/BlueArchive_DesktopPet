import { app } from 'electron';
import type { Settings } from './shared';
export const startupAppId='local.bluearchive.desktoppet';
const name=startupAppId,args=['--login-start'];
function readStartup(file:string){
 // Electron 38 parses the lookup path as a Windows command line; quote spaces.
 const v=app.getLoginItemSettings({path:`"${file}"`,args});
 const item=v.launchItems.find(i=>i.name===name&&i.scope==='user');
 return {registered:v.openAtLogin,enabled:v.openAtLogin&&!!item?.enabled};
}
export function startupStatus(){
 if(process.env.BA_TEST_DATA||!app.isPackaged)return {available:false,registered:false,enabled:false};
 return {available:true,...readStartup(process.execPath)};
}
export function setStartup(enabled:boolean,s:Settings){
 if(process.env.BA_TEST_DATA||!app.isPackaged)throw Error('开发／测试实例不会修改 Windows 启动项，请在正式程序中设置。');
 app.setLoginItemSettings({name,path:process.execPath,args,openAtLogin:enabled,enabled});
 const actual=startupStatus();if(actual.registered!==enabled)throw Error('Windows 未保存启动项设置');
 s.startupEnabled=enabled;s.startupPath=enabled?process.execPath:'';return actual;
}
export function relocateStartup(s:Settings){
 if(!s.startupEnabled||!s.startupPath||s.startupPath===process.execPath||process.env.BA_TEST_DATA||!app.isPackaged)return;
 const old=readStartup(s.startupPath);
 // An externally removed registration is not recreated. A disabled one stays disabled.
 if(!old.registered){s.startupEnabled=false;return;}
 app.setLoginItemSettings({name,path:process.execPath,args,openAtLogin:true,enabled:old.enabled});s.startupPath=process.execPath;
}
