import {PopupMenu} from './popup-menu';
import {characterGroup} from './library';
import { app, BrowserWindow, ipcMain, Menu, Tray, nativeImage, screen, powerMonitor, dialog, type MenuItemConstructorOptions } from 'electron';
import { readFileSync, writeFileSync, renameSync, mkdirSync, readdirSync, appendFileSync,copyFileSync,existsSync } from 'node:fs';
import path from 'node:path';
import {defaultProfile,normalizeProfile,pickEntry,stepError,type ActionEntry,type PlaybackStatus,type PlaybackRequest} from './activities';
import {startupStatus,setStartup,relocateStartup,startupAppId} from './startup';
import {RangeEditor} from './range-editor';
import {installWheelForwarding} from './wheel-forwarder';
import { defaults, normalizeSettings, clampSize, fitWindow, roamLimits, validateCharacter, type Settings, type Character, type Point, type PanelState, type Furniture } from './shared';

const isolatedData=process.env.BA_TEST_DATA?path.resolve(process.env.BA_TEST_DATA):!app.isPackaged?path.join(app.getAppPath(),'.dev-profile'):undefined;
if(isolatedData){mkdirSync(isolatedData,{recursive:true});app.setPath('userData',isolatedData);}
let win: BrowserWindow;
let tray: Tray;
let settings: Settings = normalizeSettings({});
let configPath: string;
let saveTimer: NodeJS.Timeout | undefined;
let dragOrigin: { mouse: Point; window: Point } | null = null;
let hit = true;
let ignoringMouse: boolean | undefined;
let failed = false;
let character: Character | null = null;
let model: ArrayBuffer | undefined;
let furniture: Furniture | undefined;
let loadError: string | undefined;
let costumes: { directory: string; name: string; aliases?: string[] }[] = [];
let panel: BrowserWindow | null = null;
let activity = 'loading';
let menuOpen = false;
let nextRandom = 0, nextWalk = 0, suspended = false;
let walk: { x: number; y: number; destination: number; direction: number; testing?: boolean } | null = null;
let anchor: Point | null = null;
let motionLast = Date.now();
let playbackToken=0,sequence:{entry:ActionEntry;index:number}|undefined,playback:PlaybackStatus|undefined;
let durations:Record<string,number>={},lastRandom:Record<string,string>={};
let rangeEditor:RangeEditor;
let popupMenu:PopupMenu;
let quitting=false,cleanedUp=false,editorDirty=false;
let ticker:NodeJS.Timeout|undefined,metricsTimer:NodeJS.Timeout|undefined;
app.setAppUserModelId(startupAppId);
const windowAlive=()=>!!win&&!win.isDestroyed()&&!win.webContents.isDestroyed();
function cleanup(){
 if(cleanedUp)return;cleanedUp=true;
 clearInterval(ticker);clearInterval(metricsTimer);clearTimeout(saveTimer);
 if(windowAlive()){const b=win.getBounds();settings.position={x:b.x,y:b.y};}
 walk=null;dragOrigin=null;sequence=undefined;rangeEditor?.close();popupMenu?.close();
 if(configPath)saveNow();if(tray&&!tray.isDestroyed())tray.destroy();
}
const thumbnails=new Map<string,string|null>();
const displayLayout=()=>JSON.stringify(screen.getAllDisplays().map(d=>({id:d.id,bounds:d.bounds,workArea:d.workArea,scale:d.scaleFactor})).sort((a,b)=>a.id-b.id));
const onscreen=()=>screen.getAllDisplays().some(d=>{const b=win.getBounds(),a=d.workArea;return b.x+b.width>a.x&&b.x<a.x+a.width&&b.y+b.height>a.y&&b.y<a.y+a.height;});
function profile(){return settings.profiles[settings.character] ||= defaultProfile(character!);}
function asset(furnitureId?:string){
 if(!character)throw Error('角色未加载');const f=furnitureId?character.furniture?.find(f=>f.id===furnitureId):undefined;if(furnitureId&&!f)throw Error('家具不存在');
 const root=process.env.BA_CHARACTERS||(app.isPackaged?path.join(process.resourcesPath,'characters'):path.join(app.getAppPath(),'characters'));
 const bytes=readFileSync(path.join(root,settings.character,f?.model||character.model));if(bytes.length<20||bytes.toString('ascii',0,4)!=='glTF'||bytes.readUInt32LE(4)!==2||bytes.readUInt32LE(8)!==bytes.length)throw Error('GLB 文件损坏');
 return {character,furniture:f,model:bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength) as ArrayBuffer};
}
function cancelPlayback(restore=true){playbackToken++;sequence=undefined;playback=undefined;if(restore){furniture=undefined;activity='pending';win.webContents.send('pet:playback',{token:playbackToken} satisfies PlaybackRequest);}deferAutomatic();updatePanel();}
function nextStep(){
 if(!sequence)return;const step=sequence.entry.steps[sequence.index];if(!step){cancelPlayback();return;}
 const token=++playbackToken;furniture=step.kind==='furniture'?character?.furniture?.find(f=>f.id===step.id):undefined;
 playback={token,entry:sequence.entry.name,index:sequence.index,total:sequence.entry.steps.length,phase:'loading'};
 win.webContents.send('pet:playback',{token,step,next:sequence.entry.steps[sequence.index+1]} satisfies PlaybackRequest);updatePanel();refreshMenu();
}
function playEntry(entry:ActionEntry){if(!character||entry.steps.some(s=>stepError(s,character!)))throw Error('组合包含不可用动作');pauseAutomatic();cancelPlayback(false);sequence={entry:structuredClone(entry),index:0};loadError=undefined;setVisible(true);nextStep();}
function randomEntry(){const e=pickEntry(profile(),character!,lastRandom[settings.character]);if(!e)throw Error('启用的动作组中没有可用条目');lastRandom[settings.character]=e.id;playEntry(e);}
function deferAutomatic() { nextRandom = Date.now() + settings.randomInterval * 1000 * (0.8 + Math.random() * 0.4); nextWalk = Date.now() + 8000 + Math.random() * 12000; }
function stopWalk() {
  if (!walk) return;
  walk = null;
  if(!windowAlive())return;
  const bounds = win.getBounds(); settings.position = { x: bounds.x, y: bounds.y }; persist();
  win.webContents.send('pet:roam', 0);
}
function pauseAutomatic() { stopWalk(); deferAutomatic(); }
function panelState(): PanelState {
  const root = process.env.BA_CHARACTERS || (app.isPackaged ? path.join(process.resourcesPath, 'characters') : path.join(app.getAppPath(), 'characters'));
  return { ready: activity !== 'loading' && !failed, settings, character, furniture, error: loadError,playback,durations,startup:startupStatus(),range:rangeEditor?.active?{radius:rangeEditor.radius,actual:rangeEditor.actual}:undefined, characters: costumes.map(c => {
    let thumbnail: string | null = null;
    if(thumbnails.has(c.directory))thumbnail=thumbnails.get(c.directory)!;
    else {try { thumbnail = 'data:image/png;base64,' + readFileSync(path.join(root, c.directory, 'thumbnail.png')).toString('base64'); } catch {} thumbnails.set(c.directory,thumbnail);}
    return { id: c.directory, name: c.name, ...(c.aliases?.length ? { aliases: c.aliases } : {}), thumbnail };
  }) };
}
function updatePanel() { if (!quitting && panel && !panel.isDestroyed()&&!panel.webContents.isDestroyed()) panel.webContents.send('panel:state', panelState()); }
function openPanel() {
  pauseAutomatic();
  if (panel && !panel.isDestroyed()) { panel.show(); panel.focus(); return; }
  panel = new BrowserWindow({ width: 1200, height: 820, minWidth: 820, minHeight: 600, title: '蔚蓝档案 · 桌宠设置', backgroundColor: '#eff5fa', autoHideMenuBar: true, webPreferences: { preload: path.join(__dirname, 'panel-preload.cjs'), contextIsolation: true, nodeIntegration: false, sandbox: true } });
  panel.webContents.on('will-prevent-unload',event=>{if(quitting||dialog.showMessageBoxSync(panel!,{type:'question',buttons:['继续编辑','放弃修改'],defaultId:0,cancelId:0,message:'动作组合尚未保存，是否放弃修改？'})===1){editorDirty=false;event.preventDefault();}});
  panel.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  panel.webContents.on('before-input-event',(event,input)=>{if(input.type==='keyDown'&&input.key==='Escape'&&rangeEditor?.active){event.preventDefault();rangeEditor.close();}});
  panel.webContents.on('will-navigate', e => e.preventDefault());
  panel.on('closed', () => { panel = null; editorDirty=false;deferAutomatic(); });
  void panel.loadFile(path.join(__dirname, 'panel.html'));
}
function actionMenu(): MenuItemConstructorOptions[] {
  const groups = new Map<string, MenuItemConstructorOptions[]>();
  for (const action of character?.actions || []) {
    const group = action.category || '常用';
    if (!groups.has(group)) groups.set(group, []);
    groups.get(group)!.push({ label: action.label, id: `action-${action.id}`, click: () => triggerAction(action.id) });
  }
  return [...(groups.get('常用') || []), ...Array.from(groups).filter(([name]) => name !== '常用').map(([label, submenu]) => ({label, submenu}))];
}
function triggerAction(id: string) {playEntry({id:'manual',name:character?.actions?.find(a=>a.id===id)?.label||id,steps:[{kind:'action',id,mode:'count',value:1,gap:0}]});}
function switchFurniture(id?: string) {
  const selected = id ? character?.furniture?.find(f => f.id === id) : undefined;
  if (!character || (id && !selected) || (activity === 'loading' && !failed)) return;
  pauseAutomatic();cancelPlayback(false);furniture=selected;loadError=undefined;failed=false;setVisible(true);
  win.webContents.send('pet:playback',{token:playbackToken,step:selected?{kind:'furniture',id:selected.id,mode:'count',value:1,gap:0}:undefined,continuous:!!selected} satisfies PlaybackRequest);updatePanel();refreshMenu();return;

}
function automaticTick() {
  if(quitting||!windowAlive())return;
  if (furniture||sequence||rangeEditor?.active) return;
  const now = Date.now(), dt = Math.min((now - motionLast) / 1000, 0.1); motionLast = now;
  if (suspended || failed || !win.isVisible() || (panel?.isVisible() && !walk?.testing) || menuOpen || dragOrigin || hit || activity === 'loading') { if (walk) pauseAutomatic(); return; }
  if (walk) {
    if (!settings.roaming && !walk.testing) { pauseAutomatic(); return; }
    walk.x += walk.direction * settings.roamSpeed * dt;
    const finished = walk.direction > 0 ? walk.x >= walk.destination : walk.x <= walk.destination;
    if (finished) walk.x = walk.destination;
    win.setBounds({ x: Math.round(walk.x), y: walk.y, ...sizeOf() }, false);
    if (finished) { stopWalk(); nextWalk = now + 8000 + Math.random() * 12000; }
    return;
  }
  if (activity !== 'idle') return;
  if (settings.randomIdle && now >= nextRandom) {
    nextRandom = now + settings.randomInterval * 1000 * (0.8 + Math.random() * 0.4);
    try{randomEntry();}catch{/* An empty enabled pool stays idle. */}
    return;
  }
  if (settings.roaming && onscreen() && now >= nextWalk && character?.actions?.some(a => a.id === 'walk')) {
    const bounds = win.getBounds(); anchor ||= { x: bounds.x, y: bounds.y };
    const area = screen.getDisplayMatching(bounds).workArea;
    const limits = roamLimits(anchor.x, settings.roamRadius, area, sizeOf().width);
    const destination = Math.round(limits.min + Math.random() * (limits.max - limits.min));
    nextWalk = now + 8000 + Math.random() * 12000;
    if (Math.abs(destination - bounds.x) < 24) return;
    walk = { x: bounds.x, y: bounds.y, destination, direction: destination > bounds.x ? 1 : -1 };
    win.webContents.send('pet:roam', walk.direction);
  }
}
const sizeOf = () => ({ width: Math.round(settings.size * 1.5), height: Math.round(settings.size * 1.45) });
function persist() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(saveNow, 250);
}
function saveNow() {
  try { mkdirSync(path.dirname(configPath), { recursive: true }); writeFileSync(configPath + '.tmp', JSON.stringify(settings, null, 2)); renameSync(configPath + '.tmp', configPath); }
  catch (error) { console.error('Settings save failed', error); }
}
function recover(reset = false,force=false) {
  if(quitting||!windowAlive())return;
  pauseAutomatic(); anchor = null;
  const size = sizeOf();
  const layout=displayLayout();force ||= !!settings.displayLayout&&settings.displayLayout!==layout;settings.displayLayout=layout;
  settings.position = settings.allowOffscreen&&!reset&&!force&&settings.position?settings.position:fitWindow(reset ? null : settings.position, size.width, size.height, screen.getAllDisplays().map(d => d.workArea));
  win.setBounds({ ...settings.position, ...size });
  persist();
}
function broadcast() { if(quitting||!windowAlive())return;win.webContents.send('pet:settings', settings); updatePanel(); }
function changeSize(size: number) {
  if (!Number.isFinite(size)) return;
  pauseAutomatic(); settings.size = clampSize(size); recover(); broadcast(); refreshMenu();
}
function applyHit(force=false) {
  const ignore = !(hit || failed || dragOrigin);
  if (!win.isDestroyed() && (force||ignoringMouse !== ignore)) {
    win.setIgnoreMouseEvents(ignore, { forward: true });
    ignoringMouse = ignore;
  }
}
function setVisible(visible: boolean) {
  if(quitting||!windowAlive())return;
  if (!visible) pauseAutomatic();
  if (visible) { win.showInactive(); win.setAlwaysOnTop(settings.alwaysOnTop, 'screen-saver'); }
  else { dragOrigin = null; win.hide(); }
  win.webContents.send('pet:visibility', visible); refreshMenu();
}
function resetOrientation(){pauseAutomatic();settings.yaw=0;settings.pitch=0;settings.roll=0;persist();broadcast();}
function refreshMenu() {
  if(quitting||!windowAlive())return Menu.buildFromTemplate([]);
  const favoriteActions=character?.actions?.filter(a=>settings.favorites.includes(settings.character+':'+a.id))||[];
  const menu = Menu.buildFromTemplate([
    { label: character ? `蔚蓝档案 · ${character.name}` : '蔚蓝档案桌宠', enabled: false },
    { type: 'separator' },
    { id: 'open-panel', label: '角色与动作面板…', click: openPanel },
    { id: 'costumes', label: '角色／服装', submenu: costumes.map(costume => ({ id: `costume-${costume.directory}`, label: costume.name, type: 'radio' as const, checked: costume.directory === settings.character, click: () => switchCostume(costume.directory) })) },
    {id:'favorite-actions',label:'常用动作',enabled:!!character&&!failed,submenu:favoriteActions.length?favoriteActions.map(a=>({id:'favorite-'+a.id,label:a.label,enabled:activity!=='loading',click:()=>triggerAction(a.id)})):[{label:'在动作面板点击星号添加',enabled:false}]},
    { id: 'actions', label: '动作', enabled: !!character && !failed, submenu: actionMenu() },
    { id: 'furniture', label: '家具互动', enabled: !!character, submenu: [...(character?.furniture || []).map(f => ({ id: `furniture-${f.id}`, label: f.name, type: 'radio' as const, checked: furniture?.id === f.id, enabled: activity !== 'loading', click: () => switchFurniture(f.id) })), { label: '收起家具，恢复桌宠', id: 'furniture-close', enabled: !!furniture && (activity !== 'loading' || failed), click: () => switchFurniture() }] },
    { id:'visibility', label: win.isVisible() ? '隐藏桌宠' : '显示桌宠', click: () => setVisible(!win.isVisible()) },
    { id: 'always-on-top', label: '始终置顶', type: 'checkbox', checked: settings.alwaysOnTop, click: item => { settings.alwaysOnTop = item.checked; win.setAlwaysOnTop(item.checked, 'screen-saver'); persist(); broadcast(); } },
    { id: 'size', label: '角色大小', submenu: [200, 280, 360, 440].map(size => ({ label: `${size} 像素`, type: 'radio' as const, checked: settings.size === size, click: () => changeSize(size) })) },
    { id:'orientation', label:'XYZ 旋转', submenu:[
      ...(['pitch','yaw','roll'] as const).flatMap((axis,index)=>[-1,1].map(sign=>({id:`rotate-${axis}-${sign}`,label:`${['X · 俯仰','Y · 水平','Z · 侧倾'][index]} ${sign>0?'+':'−'}15°`,click:()=>{pauseAutomatic();settings[axis]+=sign*Math.PI/12;persist();broadcast();}}))),
      {id:'view-reset',label:'恢复角度',click:resetOrientation}
    ]},
    { id:'recover', label:'找回桌宠', click:()=>{recover(true);setVisible(true);} },
    { id: 'help', label: '操作说明', click: () => { void dialog.showMessageBox(win, { title: '蔚蓝档案桌宠', message: '左键拖动：移动桌宠\n单击：互动动作\n滚轮：调整大小\nShift＋拖动：水平旋转\nCtrl＋上下拖动：X 轴旋转\nAlt＋左右拖动：Z 轴旋转\n三轴可连续旋转多圈\n右键：菜单\n\n空白区域鼠标穿透。系统托盘可找回、隐藏或退出。', type: 'info' }); } },
    { type: 'separator' },
    { id: 'quit', label: '退出', click: () => app.quit() }
  ]);
  menu.on('menu-will-show', () => { pauseAutomatic(); menuOpen = true; });
  menu.on('menu-will-close', () => { menuOpen = false; deferAutomatic(); });
  tray.setContextMenu(menu);
  return menu;
}
function switchCostume(directory: string) {
  if (!costumes.some(c => c.directory === directory) || (directory === settings.character && !failed)) return;
  pauseAutomatic();
  cancelPlayback(false);rangeEditor?.close();durations={};
  const previousActivity = activity; activity = 'loading';
  const previous = { character, model, loadError, failed, directory: settings.character };
  loadCharacter(directory);
  if (failed) {
    const message = loadError || '服装加载失败';
    ({ character, model, loadError, failed } = previous); settings.character = previous.directory;
    activity = previousActivity; updatePanel();
    refreshMenu(); void dialog.showMessageBox(win, { type: 'error', message }); return;
  }
  furniture = undefined;
  dragOrigin = null; hit = true; applyHit(); persist();
  // Reload releases the old WebGL context and all costume resources together.
  win.webContents.reload(); setVisible(true); updatePanel();
}
function loadCharacter(requested?: string) {
  character = null; model = undefined; loadError = undefined; failed = false;
  const root = process.env.BA_CHARACTERS || (app.isPackaged ? path.join(process.resourcesPath, 'characters') : path.join(app.getAppPath(), 'characters'));
  const errors: string[] = [];
  try {
    const dirs = readdirSync(root, { withFileTypes: true }).filter(d => d.isDirectory());
    costumes = [];
    for (const dir of dirs) {
      try {
        const candidate = validateCharacter(JSON.parse(readFileSync(path.join(root, dir.name, 'character.json'), 'utf8')));
        costumes.push({ directory: dir.name, name: candidate.name, aliases: candidate.aliases });
      } catch { /* Invalid packs are reported by the normal loading path. */ }
    }
    dirs.sort((a, b) => Number(b.name === settings.character) - Number(a.name === settings.character) || a.name.localeCompare(b.name));
    for (const dir of dirs) {
      if (requested && dir.name !== requested) continue;
      try {
        const candidate = validateCharacter(JSON.parse(readFileSync(path.join(root, dir.name, 'character.json'), 'utf8')));
        const bytes = readFileSync(path.join(root, dir.name, candidate.model));
        if (bytes.toString('ascii', 0, 4) !== 'glTF' || bytes.readUInt32LE(4) !== 2 || bytes.readUInt32LE(8) !== bytes.length) throw new Error('GLB 文件损坏');
        character = candidate;
        model = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer;
        settings.character = dir.name;profile();return;
      } catch (e) { errors.push(`${dir.name}: ${String(e)}`); }
    }
  } catch (e) { errors.push(String(e)); }
  loadError = errors.length ? `角色加载失败：\n${errors.join('\n')}` : '尚未安装已验证的原版角色包。\n请将角色包放入 characters 目录后重新启动。';
  failed = true;
}

if (!app.requestSingleInstanceLock()) app.quit();
else {
  app.on('second-instance', () => { if (windowAlive()) { recover(); setVisible(true); } });
  app.whenReady().then(() => {
    configPath = path.join(app.getPath('userData'), 'settings.json');
    try { const raw=JSON.parse(readFileSync(configPath,'utf8'));if(raw.version!==2&&!existsSync(configPath+'.v1.bak'))copyFileSync(configPath,configPath+'.v1.bak');settings=normalizeSettings(raw); } catch { /* First launch or damaged config. */ }
    try{relocateStartup(settings);}catch(error){console.error('启动项路径更新失败',error);}
    loadCharacter();
    win = new BrowserWindow({ ...sizeOf(), frame: false, transparent: true, resizable: false, maximizable: false, hasShadow: false, skipTaskbar: true, alwaysOnTop: settings.alwaysOnTop, show: false, backgroundColor: '#00000000', webPreferences: { preload: path.join(__dirname, 'preload.cjs'), contextIsolation: true, nodeIntegration: false, sandbox: true, backgroundThrottling: true } });
    installWheelForwarding(win,()=>settings.wheelPassThrough&&!dragOrigin,()=>{if(windowAlive())applyHit(true);});
    win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
    win.webContents.on('will-navigate', event => event.preventDefault());
    const pixels = Buffer.alloc(24 * 24 * 4);
    for (let y = 0; y < 24; y++) for (let x = 0; x < 24; x++) { const i = (y * 24 + x) * 4; const r = Math.hypot(x - 11.5, y - 11.5); pixels[i] = 240; pixels[i+1] = 180; pixels[i+2] = 50; pixels[i+3] = r > 6 && r < 10 ? 255 : 0; }
    tray = new Tray(nativeImage.createFromBitmap(pixels, { width: 24, height: 24, scaleFactor: 1 }));
    tray.setToolTip('蔚蓝档案桌宠'); tray.on('double-click', () => setVisible(!win.isVisible()));
    popupMenu=new PopupMenu(open=>{menuOpen=open;if(open)pauseAutomatic();else if(!quitting)deferAutomatic();});
    rangeEditor=new RangeEditor(()=>win.getBounds(),()=>updatePanel(),radius=>{settings.roamRadius=radius;persist();broadcast();});
    refreshMenu(); recover();
    // Only the app's main frame may invoke the bridge.
    const trusted = (event: Electron.IpcMainEvent | Electron.IpcMainInvokeEvent) => !quitting&&windowAlive()&&event.sender === win.webContents && event.senderFrame === win.webContents.mainFrame;
    deferAutomatic();
    const panelTrusted = (e: Electron.IpcMainInvokeEvent|Electron.IpcMainEvent) => !quitting&&!!panel&&!panel.isDestroyed() && e.sender === panel.webContents && e.senderFrame === panel.webContents.mainFrame;
    ipcMain.on('panel:dirty',(e,value)=>{if(panelTrusted(e)&&typeof value==='boolean')editorDirty=value;});
    ipcMain.handle('panel:state', e => { if (!panelTrusted(e)) throw new Error('Invalid sender'); return panelState(); });
    ipcMain.handle('panel:command', (e, command, value) => {
      if (!panelTrusted(e)) throw new Error('Invalid sender');
      if (command === 'select' && typeof value === 'string') switchCostume(value);
      else if (command === 'furniture' && typeof value === 'string') switchFurniture(value || undefined);
      else if (command === 'action' && typeof value === 'string' && activity !== 'loading' && character?.actions?.some(a => a.id === value)) triggerAction(value);
      else if (command === 'favorite' && typeof value === 'string' && character?.actions?.some(a => a.id === value)) {
        const key = settings.character + ':' + value; settings.favorites = settings.favorites.includes(key) ? settings.favorites.filter(k => k !== key) : [...settings.favorites, key]; persist();
      } else if(command==='favorite-character'&&typeof value==='string'&&costumes.some(c=>c.directory===value)){
        const name=characterGroup(costumes.find(c=>c.directory===value)!.name);settings.favoriteCharacters=settings.favoriteCharacters.includes(name)?settings.favoriteCharacters.filter(n=>n!==name):[...settings.favoriteCharacters,name];persist();
      } else if (command === 'settings' && value && typeof value === 'object') {
        pauseAutomatic();
        const patch:Record<string,unknown>={};for(const key of ['yaw','pitch','roll','contextMenu','actionSort','eyeFollow','randomIdle','randomInterval','roaming','roamRadius','roamSpeed','theme','wheelPassThrough','outline','outlineWidth','allowOffscreen','playbackSpeed','transitionSpeed','speedOverrides','size','alwaysOnTop'])if(Object.hasOwn(value,key))patch[key]=value[key];
        const oldSize=settings.size,oldOffscreen=settings.allowOffscreen;settings=normalizeSettings({...settings,...patch});
        if(settings.size!==oldSize||oldOffscreen!==settings.allowOffscreen)recover();win.setAlwaysOnTop(settings.alwaysOnTop,'screen-saver');persist();deferAutomatic();broadcast();refreshMenu();
      } else if(command==='profile-save'){
        settings.profiles[settings.character]=normalizeProfile(value);persist();
      } else if(command==='preview'){
        const entry=normalizeProfile({entries:[value],groups:[]}).entries[0];playEntry(entry);
      } else if(command==='startup'&&typeof value==='boolean'){
        setStartup(value,settings);saveNow();
      } else if(command==='range-open'){
        if(!onscreen())throw Error('请先找回桌宠，再调整走动范围');pauseAutomatic();rangeEditor.open(settings.roamRadius);
      } else if(command==='range-cancel'){rangeEditor.close();
      } else if (command === 'test-random' && activity !== 'loading' && !failed) {
        randomEntry();
      } else if (command === 'test-walk' && activity !== 'loading' && !failed && !furniture) {
        if(!onscreen())throw Error('屏幕外暂停自动走动，请先找回桌宠');cancelPlayback(false);rangeEditor.close();
        if (!character?.actions?.some(a => a.id === 'walk')) throw new Error('此角色没有原版走路动画');
        pauseAutomatic(); setVisible(true);
        const bounds = win.getBounds(), area = screen.getDisplayMatching(bounds).workArea;
        anchor ||= { x: bounds.x, y: bounds.y };
        const limits = roamLimits(anchor.x, settings.roamRadius, area, sizeOf().width);
        const direction = limits.max - bounds.x >= bounds.x - limits.min ? 1 : -1;
        const destination = Math.round(direction > 0 ? Math.min(limits.max, bounds.x+80) : Math.max(limits.min, bounds.x-80));
        if (Math.abs(destination-bounds.x) < 8) throw new Error('当前位置空间不足，请先移动角色或调小角色大小');
        walk = {x:bounds.x,y:bounds.y,destination,direction,testing:true}; win.webContents.send('pet:roam',direction);
      } else if (command === 'stop-test') { pauseAutomatic();cancelPlayback();
      } else if(command==='reset-orientation'){resetOrientation();
      } else if (command === 'recover') { recover(true); setVisible(true); }
      updatePanel(); return panelState();
    });
    ipcMain.on('pet:activity', (e, id) => { if (trusted(e) && typeof id === 'string' && (['idle','manual','sequence'].includes(id) || character?.actions?.some(a => a.id === id))) {if(id==='manual')cancelPlayback(false);const wasLoading = activity === 'loading'; activity = id; if (wasLoading) { updatePanel(); refreshMenu(); } } });
    ipcMain.handle('pet:asset',(e,id)=>{if(!trusted(e)||(id!==undefined&&typeof id!=='string'))throw Error('Invalid sender or asset');return asset(id);});
    ipcMain.on('pet:durations',(e,values)=>{if(!trusted(e)||!values||typeof values!=='object')return;for(const [key,v] of Object.entries(values).slice(0,600))if(/^(action|furniture):[a-z0-9_-]+$/.test(key)&&typeof v==='number'&&Number.isFinite(v)&&v>0)durations[key]=v;updatePanel();});
    ipcMain.on('pet:playback-event',(e,token,event,error)=>{
      if(!trusted(e)||token!==playbackToken)return;
      if(event==='error'){const restore=!!furniture||!!sequence;loadError=`动作加载失败：${String(error).slice(0,1000)}`;cancelPlayback(restore);if(!restore)failed=true;updatePanel();return;}
      if(event==='ready'){activity=sequence?'sequence':'idle';if(!sequence&&!furniture)deferAutomatic();if(playback)playback.phase='playing';updatePanel();refreshMenu();}
      if(event==='gap'&&playback){playback.phase='gap';updatePanel();}
      if(event==='done'&&sequence){sequence.index++;nextStep();}
    });
    ipcMain.on('pet:touch', e => { if (trusted(e)) pauseAutomatic(); });
    ipcMain.handle('pet:init', e => { if (!trusted(e)) throw new Error('Invalid sender'); return { settings, character, furniture, model, error: loadError }; });
    ipcMain.on('pet:hit', (e, value) => { if (trusted(e) && typeof value === 'boolean') { hit = value; if (hit) pauseAutomatic(); applyHit(); } });
    ipcMain.on('pet:drag', (e, active) => {
      if (!trusted(e) || typeof active !== 'boolean') return;
      pauseAutomatic(); anchor = null;
      if(active&&!furniture)cancelPlayback(false);
      dragOrigin = active ? { mouse: screen.getCursorScreenPoint(), window: { x: win.getBounds().x, y: win.getBounds().y } } : null;
      if (!active) { settings.position = { x: win.getBounds().x, y: win.getBounds().y }; recover(); }
      applyHit();
    });
    ipcMain.on('pet:resize', (e, value) => { if (trusted(e) && typeof value === 'number') changeSize(value); });
    ipcMain.on('pet:rotate',(e,yaw,pitch,roll)=>{if(trusted(e)&&Number.isFinite(yaw)&&(pitch===undefined||Number.isFinite(pitch))&&(roll===undefined||Number.isFinite(roll))){settings.yaw=yaw;if(pitch!==undefined)settings.pitch=pitch;if(roll!==undefined)settings.roll=roll;persist();updatePanel();}});
    ipcMain.on('pet:menu',e=>{if(trusted(e)&&!quitting)popupMenu.open(win,refreshMenu(),character?.name||'桌宠菜单',settings.theme,settings.contextMenu);});
    ipcMain.on('pet:error', (e, value) => { if (trusted(e) && typeof value === 'string') { failed = true; loadError = value.slice(0, 3000); pauseAutomatic(); applyHit(); updatePanel(); refreshMenu(); console.error(loadError); } });
    let cursorWasInside = false;
    let tick = 0;
    ticker = setInterval(() => {
      if(quitting||!windowAlive())return;
      automaticTick();
      if (dragOrigin) {
        const cursor = screen.getCursorScreenPoint();
        const x = Math.round(dragOrigin.window.x + cursor.x - dragOrigin.mouse.x);
        const y = Math.round(dragOrigin.window.y + cursor.y - dragOrigin.mouse.y);
        const current = win.getBounds();
        // setPosition internally round-trips the current native size. At
        // fractional Windows DPI this can accumulate a pixel on every move,
        // stretching the transparent canvas even with resizable:false.
        const size = sizeOf();
        if (current.x !== x || current.y !== y || Math.abs(current.width - size.width) > 1 || Math.abs(current.height - size.height) > 1) win.setBounds({ x, y, ...size }, false);
      } else if (++tick % 2 === 0 && win.isVisible()) {
        // Some Windows compositors do not forward movement into an ignored
        // window. Poll only our rectangle to reliably restore character input.
        const cursor = screen.getCursorScreenPoint();
        const bounds = win.getBounds();
        const x = cursor.x - bounds.x, y = cursor.y - bounds.y;
        const inside = x >= 0 && y >= 0 && x < bounds.width && y < bounds.height;
        if (inside || cursorWasInside || settings.eyeFollow) win.webContents.send('pet:cursor', { x, y });
        cursorWasInside = inside;
      }
    }, 16);
    win.on('blur', () => { if (!quitting&&windowAlive()&&dragOrigin) { dragOrigin = null; settings.position = { x: win.getBounds().x, y: win.getBounds().y }; recover(); applyHit(); } });
    screen.on('display-added', () => {rangeEditor.close();recover(false,true);});
    screen.on('display-removed', () => {rangeEditor.close();recover(false,true);});
    screen.on('display-metrics-changed', () => {rangeEditor.close();recover(false,true);});
    powerMonitor.on('suspend', () => { if(quitting||!windowAlive())return;suspended = true; pauseAutomatic();win.webContents.send('pet:visibility',false); });
    powerMonitor.on('resume', () => { if(quitting||!windowAlive())return;suspended = false; recover(); win.webContents.send('pet:visibility', win.isVisible()); });
    win.once('ready-to-show', () => setVisible(true));
    win.webContents.on('render-process-gone', (_event, details) => { if(quitting||!windowAlive())return;failed = true; console.error('Renderer stopped', details); void dialog.showMessageBox({ type: 'error', message: '桌宠渲染进程已停止，请退出后重新启动。系统托盘仍可退出。' }); });
    void win.loadFile(path.join(__dirname, 'index.html'));
    win.on('close',event=>{if(!quitting){event.preventDefault();app.quit();}});
    win.on('closed',()=>{quitting=true;cleanup();if(panel&&!panel.isDestroyed())panel.destroy();app.quit();});
    app.on('before-quit',event=>{if(quitting)return;if(editorDirty&&panel&&!panel.isDestroyed()&&dialog.showMessageBoxSync(panel,{type:'question',buttons:['继续编辑','放弃修改并退出'],defaultId:0,cancelId:0,message:'动作组合尚未保存，是否放弃修改并退出？'})===0){event.preventDefault();return;}quitting=true;cleanup();});
    app.on('will-quit',cleanup);
    if (process.env.BA_METRICS) {
      const file = path.resolve(process.env.BA_METRICS);
      metricsTimer = setInterval(() => { appendFileSync(file, JSON.stringify({ time: new Date().toISOString(), processes: app.getAppMetrics() }) + '\n'); }, 10000);
      app.on('will-quit',()=>clearInterval(metricsTimer));
    }
  }).catch(error => { console.error(error); app.quit(); });
}
