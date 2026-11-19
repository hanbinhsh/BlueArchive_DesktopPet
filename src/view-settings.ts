import type {PanelState} from './shared';
import {menuSections,normalizeMenu} from './menu-config';
let send:(command:string,value?:unknown)=>Promise<boolean>,state:PanelState,key='';
const el=<T extends HTMLElement=HTMLElement>(id:string)=>document.getElementById(id) as T;
export function setupViewSettings(command:typeof send){
 send=command;el('resetOrientation').onclick=()=>void send('reset-orientation');el('resetAxes').onclick=()=>void send('reset-orientation');
 for(const [axis,name] of [['pitch','X · 俯仰'],['yaw','Y · 水平'],['roll','Z · 侧倾']] as const){
  const row=document.createElement('div');row.className='axis-row';const label=document.createElement('label');label.textContent=name;label.htmlFor='angle-'+axis;
  const minus=document.createElement('button'),plus=document.createElement('button'),input=document.createElement('input'),unit=document.createElement('span');
  minus.textContent='−15°';plus.textContent='+15°';minus.setAttribute('aria-label',name+' 减少15度');plus.setAttribute('aria-label',name+' 增加15度');input.type='number';input.step='15';input.id='angle-'+axis;unit.textContent='°';
  minus.onclick=()=>void send('settings',{[axis]:state.settings[axis]-Math.PI/12});plus.onclick=()=>void send('settings',{[axis]:state.settings[axis]+Math.PI/12});
  input.onchange=()=>{const n=input.valueAsNumber;if(Number.isFinite(n))void send('settings',{[axis]:n*Math.PI/180});else input.value=String(state.settings[axis]*180/Math.PI);};row.append(label,minus,input,unit,plus);el('axes').append(row);
 }
 el('resetMenu').onclick=()=>void send('settings',{contextMenu:normalizeMenu(null)});
}
export function renderViewSettings(value:PanelState){
 state=value;for(const axis of ['pitch','yaw','roll'] as const){const input=el<HTMLInputElement>('angle-'+axis);if(document.activeElement!==input)input.value=String(Math.round(state.settings[axis]*180/Math.PI*100)/100);}
 const cfg=state.settings.contextMenu,next=JSON.stringify(cfg);if(next===key)return;key=next;
 const focus=(document.activeElement as HTMLElement)?.dataset.control;el('menuSections').replaceChildren();
 cfg.order.forEach((id,index)=>{
  const row=document.createElement('div');row.className='menu-setting-row';row.dataset.section=id;
  const label=document.createElement('label'),check=document.createElement('input'),text=document.createElement('span');check.type='checkbox';check.checked=!cfg.hidden.includes(id);check.disabled=id==='open-panel'||id==='quit';check.dataset.control=id+'-visible';text.textContent=menuSections.find(([key])=>key===id)![1];
  check.onchange=()=>void send('settings',{contextMenu:{...cfg,hidden:check.checked?cfg.hidden.filter(k=>k!==id):[...cfg.hidden,id]}});label.append(check,text);row.append(label);
  for(const [delta,symbol,title] of [[-1,'↑','上移'],[1,'↓','下移']] as const){const b=document.createElement('button');b.textContent=symbol;b.title=title;b.setAttribute('aria-label',title+text.textContent);b.dataset.control=id+'-'+delta;b.disabled=index+delta<0||index+delta>=cfg.order.length;b.onclick=()=>{const order=[...cfg.order];[order[index],order[index+delta]]=[order[index+delta],order[index]];void send('settings',{contextMenu:{...cfg,order}});};row.append(b);}
  el('menuSections').append(row);
 });
 if(focus)Array.from(el('menuSections').querySelectorAll<HTMLElement>('[data-control]')).find(x=>x.dataset.control===focus)?.focus({preventScroll:true});
}
