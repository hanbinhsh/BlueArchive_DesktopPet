import {BrowserWindow,ipcMain,screen,type Menu,type MenuItem} from 'electron';
import path from 'node:path';
import {normalizeMenu,type MenuConfig,type MenuRow,type PopupState} from './menu-config';
export class PopupMenu {
 private window:BrowserWindow|null=null;
 private choices=new Map<string,MenuItem>();
 private value:PopupState={title:'桌宠菜单',theme:'system',rows:[]};
 constructor(private changed:(open:boolean)=>void){
  const trusted=(e:Electron.IpcMainEvent|Electron.IpcMainInvokeEvent)=>!!this.window&&!this.window.isDestroyed()&&e.sender===this.window.webContents&&e.senderFrame===this.window.webContents.mainFrame;
  ipcMain.handle('popup:state',e=>{if(!trusted(e))throw Error('Invalid sender');return this.value;});
  ipcMain.on('popup:close',e=>{if(trusted(e))this.close();});
  ipcMain.on('popup:choose',(e,id)=>{if(!trusted(e)||typeof id!=='string')return;const item=this.choices.get(id);if(!item||!item.enabled||item.submenu||item.type==='separator')return;const owner=this.window?.getParentWindow();this.close();if(item.type==='checkbox')item.checked=!item.checked;item.click(item,owner??undefined,{} as Electron.KeyboardEvent);});
 }
 open(owner:BrowserWindow,menu:Menu,title:string,theme:PopupState['theme'],config:MenuConfig){
  this.close();this.choices.clear();
  let next=0;
  const row=(item:MenuItem,parentEnabled=true):MenuRow=>{const id=item.id||`item-${++next}`,enabled=parentEnabled&&item.enabled;if(enabled)this.choices.set(id,item);return {id,label:item.label,enabled,type:item.type,checked:item.checked,children:item.submenu?.items.map(child=>row(child,enabled))};};
  const cfg=normalizeMenu(config),roots=new Map(menu.items.filter(i=>i.id).map(i=>[i.id,i]));
  this.value={title,theme,rows:cfg.order.filter(id=>!cfg.hidden.includes(id)&&roots.has(id)).map(id=>row(roots.get(id)!))};
  const point=screen.getCursorScreenPoint(),area=screen.getDisplayNearestPoint(point).workArea,width=Math.min(330,area.width),height=Math.min(548,area.height);
  const w=new BrowserWindow({parent:owner,width,height,x:Math.round(Math.max(area.x,Math.min(point.x,area.x+area.width-width))),y:Math.round(Math.max(area.y,Math.min(point.y,area.y+area.height-height))),frame:false,resizable:false,maximizable:false,minimizable:false,show:false,skipTaskbar:true,alwaysOnTop:true,backgroundColor:theme==='dark'?'#172333':'#ffffff',webPreferences:{preload:path.join(__dirname,'menu-preload.cjs'),contextIsolation:true,nodeIntegration:false,sandbox:true}});
  this.window=w;this.changed(true);w.setMenu(null);w.setAlwaysOnTop(true,'screen-saver');
  w.webContents.setWindowOpenHandler(()=>({action:'deny'}));w.webContents.on('will-navigate',e=>e.preventDefault());
  w.once('ready-to-show',()=>{if(this.window===w&&!w.isDestroyed()){
   // Windows can add a few DIP to a frameless window at fractional DPI.
   // Clamp the actual native bounds once layout has settled.
   const b=w.getBounds();w.setPosition(Math.floor(Math.max(area.x,Math.min(b.x,area.x+area.width-b.width))),Math.floor(Math.max(area.y,Math.min(b.y,area.y+area.height-b.height))));w.show();w.focus();
  }});
  w.on('blur',()=>{if(this.window===w)this.close();});w.on('closed',()=>{if(this.window===w){this.window=null;this.choices.clear();this.changed(false);}});
  void w.loadFile(path.join(__dirname,'menu.html')).catch(()=>{if(this.window===w)this.close();});
 }
 close(){const w=this.window;if(w&&!w.isDestroyed())w.close();}
}
