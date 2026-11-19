import {normalizeMenu,type MenuConfig} from './menu-config';
import type {ActionSort} from './library';
import { normalizeProfile, speed, type ActionProfile, type SpeedOverride, type PlaybackRequest, type PlaybackStatus } from './activities';
export type Point = { x: number; y: number };
export type Rect = Point & { width: number; height: number };
export type MouthEvent = { time: number; tile: number; flipped?: boolean; reset?: boolean };
export interface Furniture { id: string; name: string; model: string; clip: string; duration: number; yaw?: number; note?: string; mouthEvents: MouthEvent[]; sceneId?: string; }
export interface Settings {
  version: 2; theme: 'system' | 'light' | 'dark'; allowOffscreen: boolean; wheelPassThrough: boolean; outline: boolean; outlineWidth: number; startupEnabled: boolean; startupPath: string; displayLayout: string;
  playbackSpeed: number; transitionSpeed: number; speedOverrides: Record<string, SpeedOverride>; profiles: Record<string, ActionProfile>;
  character: string; position: Point | null; size: number; yaw: number; pitch: number; roll: number; contextMenu: MenuConfig; alwaysOnTop: boolean;
  eyeFollow: boolean; randomIdle: boolean; randomInterval: number; roaming: boolean; roamRadius: number; roamSpeed: number; favorites: string[]; favoriteCharacters: string[]; actionSort: ActionSort;
}
export interface Character {
  id: string; name: string; model: string;
  source: { url: string; description: string };
  scale: number; yaw: number;
  framing?: { minExtent?: number; actions?: Record<string, { zoom: number; centerY: number }> };
  note?: string;
  animations: { idle: string; interact: string };
  actions?: { id: string; label: string; clip: string; category?: string; sourceName?: string }[];
  idleBlink?: { action: string; interval: number };
  furniture?: Furniture[];
  mouth?: { material: string; defaultTile: number; columns?: number; rows?: number; baseUV?: [number,number]; events: Record<string, MouthEvent[]> };
}
export const defaults: Settings = { version:2,theme:'system',allowOffscreen:false,wheelPassThrough:false,outline:false,outlineWidth:38,startupEnabled:false,startupPath:'',displayLayout:'',playbackSpeed:1,transitionSpeed:1,speedOverrides:{},profiles:{},character: '', position: null, size: 280, yaw: 0, pitch: 0, roll:0, contextMenu:normalizeMenu(null), alwaysOnTop: true, eyeFollow: false, randomIdle: false, randomInterval: 30, roaming: false, roamRadius: 160, roamSpeed: 35, favorites: [],favoriteCharacters:[],actionSort:'category' };
export const clampSize = (n: number) => Math.round(Math.max(160, Math.min(480, n)));
export function normalizeSettings(raw: Partial<Settings>): Settings {
  const profiles: Record<string,ActionProfile>={}, speedOverrides: Record<string,SpeedOverride>={};
  for(const [key,v] of Object.entries(raw.profiles||{})) if(/^[a-z0-9_-]+$/.test(key)){try{profiles[key]=normalizeProfile(v);}catch{/* Preserve valid independent profiles. */}}
  for(const [key,v] of Object.entries(raw.speedOverrides||{})) if(/^[a-z0-9_-]+$/.test(key)&&v&&typeof v==='object')speedOverrides[key]={...(v.playback!==undefined?{playback:speed(v.playback)}:{}),...(v.transition!==undefined?{transition:speed(v.transition)}:{})};
  return {
    version:2,theme:raw.theme==='light'||raw.theme==='dark'?raw.theme:'system',allowOffscreen:raw.allowOffscreen===true,wheelPassThrough:raw.wheelPassThrough===true,outline:raw.outline===true,outlineWidth:typeof raw.outlineWidth==='number'&&Number.isFinite(raw.outlineWidth)?Math.max(0,Math.min(400,Math.round(raw.outlineWidth))):38,startupEnabled:raw.startupEnabled===true,startupPath:typeof raw.startupPath==='string'?raw.startupPath:'',displayLayout:typeof raw.displayLayout==='string'?raw.displayLayout:'',playbackSpeed:speed(raw.playbackSpeed),transitionSpeed:speed(raw.transitionSpeed),profiles,speedOverrides,
    character: typeof raw.character === 'string' ? raw.character : '',
    position: raw.position && Number.isFinite(raw.position.x) && Number.isFinite(raw.position.y) ? raw.position : null,
    size: Number.isFinite(raw.size) ? clampSize(raw.size!) : defaults.size,
    yaw: Number.isFinite(raw.yaw) ? raw.yaw! : 0,
    pitch: Number.isFinite(raw.pitch) ? raw.pitch! : 0,
    roll: Number.isFinite(raw.roll) ? raw.roll! : 0, contextMenu:normalizeMenu(raw.contextMenu),
    alwaysOnTop: typeof raw.alwaysOnTop === 'boolean' ? raw.alwaysOnTop : true,
    eyeFollow: raw.eyeFollow === true,
    randomIdle: raw.randomIdle === true, randomInterval: bounded(raw.randomInterval, 15, 120, 30),
    roaming: raw.roaming === true, roamRadius: bounded(raw.roamRadius, 40, 4000, 160), roamSpeed: bounded(raw.roamSpeed, 10, 80, 35),
    actionSort:raw.actionSort==='name'||raw.actionSort==='source'?raw.actionSort:'category',
    favoriteCharacters:Array.isArray(raw.favoriteCharacters)?[...new Set(raw.favoriteCharacters.filter((v):v is string=>typeof v==='string'&&v.trim().length>0&&v.length<=80&&!/[\x00-\x1f]/.test(v)).map(v=>v.trim()))].slice(0,200):[],
    favorites: Array.isArray(raw.favorites) ? [...new Set(raw.favorites.filter(v => typeof v === 'string' && /^[a-z0-9_-]+:[a-z0-9_-]+$/.test(v)))].slice(0, 200) : []
  };
}
function bounded(value: unknown, min: number, max: number, fallback: number) { return typeof value === 'number' && Number.isFinite(value) ? Math.round(Math.max(min, Math.min(max, value))) : fallback; }
export function roamLimits(anchor: number, radius: number, area: Rect, width: number) {
  const min = Math.max(area.x, anchor - radius);
  const max = Math.min(area.x + Math.max(0, area.width - width), anchor + radius);
  return { min, max: Math.max(min, max) };
}
export function fitWindow(position: Point | null, width: number, height: number, areas: Rect[]): Point {
  const area = (position && areas.find(a => position.x + width / 2 >= a.x && position.x + width / 2 <= a.x + a.width && position.y + height / 2 >= a.y && position.y + height / 2 <= a.y + a.height)) || areas[0];
  const p = position || { x: area.x + area.width - width - 24, y: area.y + area.height - height - 24 };
  return { x: Math.round(Math.max(area.x, Math.min(p.x, area.x + Math.max(0, area.width - width)))), y: Math.round(Math.max(area.y, Math.min(p.y, area.y + Math.max(0, area.height - height)))) };
}
export function validateCharacter(value: unknown): Character {
  const c = value as Character;
  if (!c || typeof c.id !== 'string' || !/^[a-z0-9_-]+$/.test(c.id) || typeof c.name !== 'string' || !c.name || typeof c.model !== 'string' || !/^[\w.-]+\.glb$/i.test(c.model) || typeof c.source?.url !== 'string' || !c.source.url || typeof c.source.description !== 'string' || !c.source.description || !(c.scale > 0 && Number.isFinite(c.scale)) || !Number.isFinite(c.yaw) || typeof c.animations?.idle !== 'string' || !c.animations.idle || typeof c.animations.interact !== 'string' || !c.animations.interact || c.animations.idle === c.animations.interact) throw new Error('角色包描述不完整或格式错误');
  if (c.note !== undefined && (typeof c.note !== 'string' || c.note.length > 500)) throw new Error('角色说明无效');
  if (c.framing !== undefined) {
    if (!c.framing || typeof c.framing !== 'object') throw new Error('角色取景配置无效');
    const { minExtent, actions } = c.framing;
    if (minExtent !== undefined && (!Number.isFinite(minExtent) || minExtent < 0 || minExtent > .01)) throw new Error('角色取景阈值无效');
    if (actions !== undefined && (!actions || typeof actions !== 'object' || Array.isArray(actions) || Object.entries(actions).some(([id, v]) => !c.actions?.some(a => a.id === id) || !v || !Number.isFinite(v.zoom) || v.zoom < .25 || v.zoom > 1 || !Number.isFinite(v.centerY) || Math.abs(v.centerY) > 5))) throw new Error('动作取景配置无效');
  }
  if (c.actions !== undefined && (!Array.isArray(c.actions) || c.actions.length > 512 || c.actions.some(a => !a || !/^[a-z0-9_-]+$/.test(a.id) || typeof a.label !== 'string' || !a.label || typeof a.clip !== 'string' || !a.clip || (a.category !== undefined && !['常用','编队与胜利','战斗','技能','移动','剧情'].includes(a.category)) || (a.sourceName !== undefined && (typeof a.sourceName !== 'string' || a.sourceName.length > 200))) || new Set(c.actions.map(a => a.id)).size !== c.actions.length)) throw new Error('动作菜单描述无效');
  if (c.actions?.some(a => (a.id === 'idle' || a.id === 'interact') && a.clip !== c.animations[a.id])) throw new Error('基础动作映射不一致');
  if (c.idleBlink && (!c.actions?.some(a => a.id === c.idleBlink!.action && a.id !== 'idle') || !Number.isFinite(c.idleBlink.interval) || c.idleBlink.interval < 1 || c.idleBlink.interval > 120)) throw new Error('待机眨眼配置无效');
  if (c.mouth) {
    if(c.mouth.baseUV!==undefined&&(!Array.isArray(c.mouth.baseUV)||c.mouth.baseUV.length!==2||c.mouth.baseUV.some(v=>!Number.isFinite(v)||v<0||v>=1)))throw new Error('口型默认偏移无效');
    for (const dimension of [c.mouth.columns, c.mouth.rows]) if (dimension !== undefined && (!Number.isInteger(dimension) || dimension < 1 || dimension > 8)) throw new Error('口型图集尺寸无效');
    if (typeof c.mouth.material !== 'string' || !c.mouth.material || !validMouthTile(c.mouth.defaultTile) || !c.mouth.events || typeof c.mouth.events !== 'object' || Array.isArray(c.mouth.events)) throw new Error('口型描述无效');
    for (const events of Object.values(c.mouth.events)) {
      if(Array.isArray(events)&&events.some(e=>e?.reset!==undefined&&typeof e.reset!=='boolean'))throw new Error('口型重置事件无效');
      if (!Array.isArray(events) || events.some((e, i) => !e || !Number.isFinite(e.time) || e.time < 0 || !validMouthTile(e.tile) || (e.flipped !== undefined && typeof e.flipped !== 'boolean') || (i > 0 && e.time < events[i - 1].time))) throw new Error('口型事件无效');
    }
  }
  if (c.furniture !== undefined && (!Array.isArray(c.furniture) || c.furniture.length > 30 || new Set(c.furniture.map(f => f.id)).size !== c.furniture.length || c.furniture.some(f => !f || !/^[a-z0-9_-]+$/.test(f.id) || !/^[\w-]+\.glb$/.test(f.model) || !f.name || !f.clip || !Number.isFinite(f.duration) || f.duration <= 0 || !Array.isArray(f.mouthEvents) || f.mouthEvents.some(e => !Number.isFinite(e.time) || e.time < 0 || !validMouthTile(e.tile))))) throw new Error('家具互动配置无效');
  if (c.furniture?.some(f => f.yaw !== undefined && !Number.isFinite(f.yaw))) throw new Error('家具视角无效');
  return c;
}
export function validMouthTile(tile: number): boolean { return Number.isInteger(tile) && tile >= 0 && Math.floor(tile / 100) < 8 && tile % 100 < 8; }
export function mouthTileAt(events: { time: number; tile: number }[], time: number, fallback: number): number {
  return mouthStateAt(events, time, fallback).tile;
}
export function mouthStateAt(events: MouthEvent[], time: number, fallback: number, looped = false) {
  const last=looped?events.at(-1):undefined;
  let state = { tile: last?.tile??fallback, flipped: last?.flipped===true };
  for (const event of events) { if (event.time > time) break; state = { tile: event.tile, flipped: event.flipped === true }; }
  return state;
}
export function mouthOffset(tile: number, base: number, columns = 8, rows = 8, flipped = false): { x: number; y: number } {
  return { x: (flipped ? tile % 100 + base % 100 + 1 : tile % 100 - base % 100) / columns, y: (Math.floor(base / 100) - Math.floor(tile / 100)) / rows };
}
// Original prefabs can use fractional tile origins (e.g. .12 rather than .125).
// Their default/reset UV stays exact; explicit SetMouthTile uses the atlas grid.
export function mouthTransform(spec:NonNullable<Character['mouth']>,events:MouthEvent[],time:number,looped=false){
 const state=mouthStateAt(events,time,spec.defaultTile,looped),cols=spec.columns??8,rows=spec.rows??8;
 if(!spec.baseUV)return {...state,...mouthOffset(state.tile,spec.defaultTile,cols,rows,state.flipped)};
 let event=looped?events.at(-1):undefined;for(const e of events){if(e.time>time)break;event=e;}
 if(!event||event.reset)return {tile:spec.defaultTile,flipped:false,x:0,y:0};
 const [u,v]=spec.baseUV;
 return {...state,x:state.flipped?(state.tile%100+1)/cols+u:state.tile%100/cols-u,y:v-Math.floor(state.tile/100)/rows};
}
export interface PetApi {
  asset(furnitureId?: string): Promise<{character:Character;furniture?:Furniture;model:ArrayBuffer}>;
  onPlayback(cb:(request:PlaybackRequest)=>void):void;
  playbackEvent(token:number,status:'ready'|'gap'|'done'|'error',error?:string):void;
  durations(values:Record<string,number>):void;
  init(): Promise<{ settings: Settings; character: Character | null; furniture?: Furniture; model?: ArrayBuffer; error?: string }>;
  hit(value: boolean): void;
  drag(active: boolean): void;
  resize(size: number): void;
  rotate(yaw: number, pitch?: number, roll?: number): void;
  menu(): void;
  activity(id: string): void;
  touch(): void;
  onRoam(cb: (direction: number) => void): void;
  report(error: string): void;
  onVisibility(cb: (visible: boolean) => void): void;
  onSettings(cb: (settings: Settings) => void): void;
  onCursor(cb: (position: Point) => void): void;
  onAction(cb: (id: string) => void): void;
}

export interface PanelState { ready: boolean; settings: Settings; characters: { id: string; name: string; thumbnail: string | null }[]; character: Character | null; furniture?: Furniture; error?: string; playback?:PlaybackStatus; durations:Record<string,number>; startup:{enabled:boolean;registered:boolean;available:boolean}; range?:{radius:number;actual:number}; }
export interface PanelApi { dirty:(value:boolean)=>void; state(): Promise<PanelState>; command(command: string, value?: unknown): Promise<PanelState>; onState(cb: (value: PanelState) => void): void; }
