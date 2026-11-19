export const menuSections = [
 ['open-panel','角色与动作面板'],['favorite-actions','常用动作（动作收藏）'],['actions','全部动作'],['costumes','角色／服装'],['furniture','家具互动'],['orientation','XYZ 旋转'],['size','角色大小'],['always-on-top','始终置顶'],['visibility','显示／隐藏'],['recover','找回桌宠'],['help','操作说明'],['quit','退出']
] as const;
export type MenuSectionId=typeof menuSections[number][0];
export interface MenuConfig {order:MenuSectionId[];hidden:MenuSectionId[]}
export function normalizeMenu(value:unknown):MenuConfig {
 const v=value&&typeof value==='object'?value as Partial<MenuConfig>:{};
 const ids=menuSections.map(([id])=>id),valid=(x:unknown):x is MenuSectionId=>typeof x==='string'&&ids.includes(x as MenuSectionId);
 const order=[...new Set([...(Array.isArray(v.order)?v.order.filter(valid):[]),...ids])];
 const hidden=[...new Set(Array.isArray(v.hidden)?v.hidden.filter(valid):[])].filter(id=>id!=='open-panel'&&id!=='quit');
 return {order,hidden};
}
export interface MenuRow {id:string;label:string;enabled:boolean;type:string;checked:boolean;children?:MenuRow[]}
export interface PopupState {title:string;theme:'system'|'light'|'dark';rows:MenuRow[]}
export interface PopupApi {state():Promise<PopupState>;choose(id:string):void;close():void}
