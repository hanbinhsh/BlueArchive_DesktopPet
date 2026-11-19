import type {Character} from './shared';
export type ActionSort='category'|'name'|'source';
type Action=NonNullable<Character['actions']>[number];
const collator=new Intl.Collator('zh-CN',{numeric:true,sensitivity:'base'});
const categories=['常用','剧情','编队与胜利','移动','战斗','技能'];
export const characterGroup=(name:string)=>name.split(/[·（(]/)[0].trim();
// Keep start/loop/end together, then use natural numeric ordering for variants.
export function compareActionNames(a:string,b:string){
 const phase=(v:string)=>{const m=v.match(/(?:^| · )(开始|持续|结束)(?= · |$)/);return {base:v.replace(/(?:^| · )(开始|持续|结束)(?= · |$)/g,''),rank:m?['开始','持续','结束'].indexOf(m[1]):-1};};
 const x=phase(a),y=phase(b);return collator.compare(x.base,y.base)||x.rank-y.rank||collator.compare(a,b);
}
export function sortActions(actions:readonly Action[],favorites:ReadonlySet<string>,mode:ActionSort):Action[]{
 return [...actions].sort((a,b)=>{
  const starred=Number(favorites.has(b.id))-Number(favorites.has(a.id));if(starred)return starred;
  if(mode==='source')return 0;
  if(mode==='name')return collator.compare(a.label,b.label)||collator.compare(a.id,b.id);
  const category=(a.category||'常用'),other=(b.category||'常用');
  const rank=(name:string)=>{const i=categories.indexOf(name);return i<0?categories.length:i;};
  const delta=rank(category)-rank(other)||collator.compare(category,other);if(delta)return delta;
  if(category==='常用'){const common=(id:string)=>{const i=['idle','interact','pickup','walk'].indexOf(id);return i<0?4:i;};const d=common(a.id)-common(b.id);if(d)return d;}
  return compareActionNames(a.label,b.label)||collator.compare(a.id,b.id);
 });
}
