import { BrowserWindow,screen,ipcMain } from 'electron';
import path from 'node:path';
import { roamLimits,type Rect } from './shared';
export class RangeEditor {
 windows:BrowserWindow[]=[];radius=160;actual=0;private dragging=0;private timer?:NodeJS.Timeout;
 constructor(private bounds:()=>Rect,private changed:()=>void,private commit:(radius:number)=>void){
  ipcMain.on('range:command',(e,command,value)=>{
   const i=this.windows.findIndex(w=>!w.isDestroyed()&&e.sender===w.webContents&&e.senderFrame===w.webContents.mainFrame);if(i<0)return;
   if(command==='start'&&(i===1||i===2))this.dragging=i===1?-1:1;
   if(command==='end')this.dragging=0;
   if(command==='radius'&&i===3&&Number.isFinite(value)){this.radius=Math.round(Math.max(40,Math.min(4000,value)));this.update();}
   if(command==='apply'){const r=this.radius;this.close();this.commit(r);}
   if(command==='cancel')this.close();
  });
 }
 get active(){return this.windows.length>0;}
 open(radius:number){this.close();this.radius=radius;
  for(const mode of ['border','left','right','tools']){const w=new BrowserWindow({width:100,height:100,transparent:true,frame:false,resizable:false,hasShadow:false,skipTaskbar:true,alwaysOnTop:true,show:false,webPreferences:{preload:path.join(__dirname,'range-preload.cjs'),contextIsolation:true,nodeIntegration:false,sandbox:true}});this.windows.push(w);w.setAlwaysOnTop(true,'screen-saver');if(mode==='border')w.setIgnoreMouseEvents(true);w.webContents.setWindowOpenHandler(()=>({action:'deny'}));w.webContents.on('will-navigate',e=>e.preventDefault());void w.loadFile(path.join(__dirname,'range.html'),{query:{mode}}).then(()=>{if(!w.isDestroyed()){this.update();w.showInactive();}}).catch(error=>{if(!w.isDestroyed())console.error('范围框加载失败',error);});}
  this.timer=setInterval(()=>{if(this.dragging){const b=this.bounds(),cursor=screen.getCursorScreenPoint();const radius=this.dragging<0?b.x-cursor.x:cursor.x-b.x-b.width;this.radius=Math.round(Math.max(40,Math.min(4000,radius)));}this.update();},40);this.changed();
 }
 update(){if(!this.active)return;const b=this.bounds(),area=screen.getDisplayMatching(b).workArea,limits=roamLimits(b.x,this.radius,area,b.width);const y=Math.max(area.y,Math.min(b.y,area.y+area.height-b.height)),height=Math.min(b.height,area.height),width=Math.max(1,limits.max-limits.min+b.width);this.actual=Math.max(0,limits.max-limits.min);
  const rects=[{x:limits.min,y,width,height},{x:limits.min,y:y+Math.round(height/2)-24,width:22,height:48},{x:limits.min+width-22,y:y+Math.round(height/2)-24,width:22,height:48},{x:Math.max(area.x,Math.min(b.x,area.x+area.width-420)),y:Math.max(area.y,Math.min(y-58,area.y+area.height-54)),width:420,height:54}];
  this.windows.forEach((w,i)=>{if(w.isDestroyed())return;const r=rects[i],old=w.getBounds();if(Object.keys(r).some(k=>(r as any)[k]!== (old as any)[k]))w.setBounds(r,false);if(i===3)w.webContents.send('range:state',{radius:this.radius,actual:this.actual});});
 }
 close(){clearInterval(this.timer);this.dragging=0;for(const w of this.windows)if(!w.isDestroyed())w.close();this.windows=[];this.changed();}
}
