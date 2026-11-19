import type { Character, Settings } from './shared';
export interface ActionStep { kind: 'action' | 'furniture'; id: string; mode: 'count' | 'seconds'; value: number; gap: number; }
export interface ActionEntry { id: string; name: string; steps: ActionStep[]; }
export interface ActionGroup { id: string; name: string; enabled: boolean; entries: string[]; }
export interface ActionProfile { entries: ActionEntry[]; groups: ActionGroup[]; }
export interface SpeedOverride { playback?: number; transition?: number; }
export interface PlaybackRequest { token: number; step?: ActionStep; next?: ActionStep; continuous?:boolean; }
export interface PlaybackStatus { token: number; entry: string; index: number; total: number; phase: 'loading' | 'playing' | 'gap'; }
const id = (v: unknown): v is string => typeof v === 'string' && /^[a-z0-9_-]{1,100}$/.test(v);
const number = (v: unknown, lo: number, hi: number) => typeof v === 'number' && Number.isFinite(v) && v >= lo && v <= hi;
export function speed(v: unknown): number { return number(v,.25,4) ? v as number : 1; }
export function effectiveSpeed(s: Settings) { return { playback: s.speedOverrides[s.character]?.playback ?? s.playbackSpeed, transition: s.speedOverrides[s.character]?.transition ?? s.transitionSpeed }; }
export function validStep(s: unknown): s is ActionStep {
 const a=s as ActionStep; return !!a && ['action','furniture'].includes(a.kind) && id(a.id) && ['count','seconds'].includes(a.mode) && number(a.value,a.mode==='count'?1:.1,a.mode==='count'?99:3600) && (a.mode!=='count'||Number.isInteger(a.value)) && number(a.gap,0,3600);
}
export function normalizeProfile(value: unknown): ActionProfile {
 const p=value as ActionProfile;
 if(!p || !Array.isArray(p.entries)||!Array.isArray(p.groups)||p.entries.length>256||p.groups.length>32) throw Error('动作组格式无效');
 if(p.entries.some(e=>!e||!id(e.id)||typeof e.name!=='string'||!e.name.trim()||e.name.length>100||!Array.isArray(e.steps)||!e.steps.length||e.steps.length>64||!e.steps.every(validStep)) || new Set(p.entries.map(e=>e.id)).size!==p.entries.length) throw Error('动作条目或步骤无效');
 if(p.groups.some(g=>!g||!id(g.id)||typeof g.name!=='string'||!g.name.trim()||g.name.length>100||typeof g.enabled!=='boolean'||!Array.isArray(g.entries)||g.entries.length>256||!g.entries.every(id))||new Set(p.groups.map(g=>g.id)).size!==p.groups.length) throw Error('动作组无效');
 return {entries:p.entries.map(e=>({id:e.id,name:e.name.trim(),steps:e.steps.map(s=>({kind:s.kind,id:s.id,mode:s.mode,value:s.value,gap:s.gap}))})),groups:p.groups.map(g=>({id:g.id,name:g.name.trim(),enabled:g.enabled,entries:[...new Set(g.entries)]}))};
}
export function stepError(s: ActionStep,c: Character): string | undefined { return (s.kind==='action'?c.actions:c.furniture)?.some(a=>a.id===s.id)?undefined:`缺少${s.kind==='action'?'动作':'家具'}：${s.id}`; }
export function eligibleEntries(p: ActionProfile,c: Character): ActionEntry[] {
 const ids=new Set(p.groups.filter(g=>g.enabled).flatMap(g=>g.entries));return p.entries.filter(e=>ids.has(e.id)&&e.steps.length&&!e.steps.some(s=>stepError(s,c)));
}
export function pickEntry(p: ActionProfile,c: Character,last?: string,random=Math.random): ActionEntry | undefined {
 let entries=eligibleEntries(p,c);if(entries.length>1)entries=entries.filter(e=>e.id!==last);return entries[Math.min(entries.length-1,Math.floor(random()*entries.length))];
}
export function defaultProfile(c: Character): ActionProfile {
 const entries:ActionEntry[]=(c.actions||[]).filter(a=>['interact','smile','blink','blink2'].includes(a.id)).map(a=>({id:'default_'+a.id,name:a.label,steps:[{kind:'action',id:a.id,mode:'count',value:1,gap:0}]}));
 const groups:ActionGroup[]=[{id:'default',name:'原版随机待机',enabled:true,entries:entries.map(e=>e.id)}];
 const sofa=['bedroom_windowsofa_start','bedroom_windowsofa_ing','bedroom_windowsofa_end'];
 if(sofa.every(id=>c.furniture?.some(f=>f.id===id))){entries.push({id:'window_rest',name:'窗边休息',steps:sofa.map((id,i)=>({kind:'furniture',id,mode:i===1?'seconds':'count',value:i===1?20:1,gap:0}))});groups.push({id:'examples',name:'家具组合示例',enabled:false,entries:['window_rest']});}
 return {entries,groups};
}
export function estimatedSeconds(e: ActionEntry,durations: Record<string,number>,playback: number): number | undefined {
 let total=0;for(const s of e.steps){const d=durations[`${s.kind}:${s.id}`];if(s.mode==='count'&&!d)return;total+=(s.mode==='seconds'?s.value:d*s.value/playback)+s.gap;}return total;
}
