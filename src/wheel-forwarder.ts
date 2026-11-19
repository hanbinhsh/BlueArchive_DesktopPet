import {app,BrowserWindow,screen} from 'electron';
import {spawn,type ChildProcessWithoutNullStreams} from 'node:child_process';
import path from 'node:path';

export function installWheelForwarding(win:BrowserWindow,enabled:()=>boolean,restoreHit:()=>void){
 let child:ChildProcessWithoutNullStreams|undefined;
 const close=()=>{const current=child;child=undefined;current?.stdin.end();current?.kill();restoreHit();};
 for(const message of [0x020a,0x020e])win.hookWindowMessage(message,(wparam,lparam)=>{
  if(!enabled()||!win.isVisible()||(wparam.readUInt32LE()&0x4000))return;
  if(!child){
   const file=app.isPackaged?path.join(process.resourcesPath,'native','wheel-forwarder.exe'):path.join(app.getAppPath(),'native','bin','wheel-forwarder.exe');
   child=spawn(file,[],{windowsHide:true,stdio:'pipe'});
   const current=child;child.on('error',error=>{console.error('滚轮转发失败',error);if(child===current)close();});
   child.on('exit',()=>{if(child===current)child=undefined;restoreHit();});
   let buffer='';child.stdout.on('data',data=>{buffer+=String(data);const lines=buffer.split('\n');buffer=lines.pop()!;for(const line of lines){
    const [kind,handle,message,wp,lp]=line.trim().split(' ');if(kind==='forwarded'||kind==='blocked')restoreHit();if(kind!=='local')continue;
    const target=BrowserWindow.getAllWindows().find(w=>!w.isDestroyed()&&w!==win&&w.getNativeWindowHandle().readBigUInt64LE().toString()===handle);if(!target||target.webContents.isDestroyed())continue;
    const word=Number(wp),location=Number(lp),point=screen.screenToDipPoint({x:(location<<16)>>16,y:location>>16}),bounds=target.getContentBounds(),delta=(word>>16)/120*100;
    target.webContents.sendInputEvent({type:'mouseWheel',x:Math.round(point.x-bounds.x),y:Math.round(point.y-bounds.y),deltaX:Number(message)===0x20e?-delta:0,deltaY:Number(message)===0x20a?delta:0,modifiers:[...(word&4?['shift' as const]:[]),...(word&8?['control' as const]:[])]});
   }});child.stderr.on('data',data=>console.error('滚轮转发：',String(data)));child.stdin.on('error',()=>{if(child===current)close();});
  }
  // Read the original Windows wheel delta, modifier keys and physical position.
  // This avoids converting touchpad/high-resolution deltas from CSS pixels.
  const hwnd=win.getNativeWindowHandle().readBigUInt64LE();
  child.stdin.write(`${hwnd} ${message} ${wparam.readUInt32LE()} ${lparam.readUInt32LE()}\n`);
 });
 win.once('closed',close);app.once('before-quit',close);
}
