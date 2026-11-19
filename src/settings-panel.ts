import {sortActions} from './library';
import type { PanelState } from './shared';
import {defaultProfile,effectiveSpeed,estimatedSeconds,stepError,type ActionProfile,type ActionEntry,type ActionStep} from './activities';
const el=<T extends HTMLElement=HTMLElement>(id:string)=>document.getElementById(id) as T;
let state:PanelState,draft:ActionProfile,characterId='',selected='',groupId='',dirty=false,send:(name:string,value?:unknown)=>Promise<boolean>;
const uid=()=>crypto.randomUUID().replaceAll('-','');
const button=(text:string,run:()=>void)=>{const b=document.createElement('button');b.textContent=text;b.onclick=run;return b;};
const sortedActions=()=>sortActions(state.character?.actions||[],new Set(state.settings.favorites.filter(k=>k.startsWith(state.settings.character+':')).map(k=>k.split(':')[1])),state.settings.actionSort);
let lastActionSort='';
let notifyDirty=(value:boolean)=>{};
function change(){dirty=true;notifyDirty(true);el<HTMLButtonElement>('saveProfile').disabled=false;el<HTMLButtonElement>('cancelProfile').disabled=false;el('dirtyState').textContent='有未保存修改';}
function reset(){draft=structuredClone(state.settings.profiles[state.settings.character]||defaultProfile(state.character!));selected=draft.entries.some(e=>e.id===selected)?selected:draft.entries[0]?.id||'';groupId=draft.groups.some(g=>g.id===groupId)?groupId:draft.groups[0]?.id||'';dirty=false;notifyDirty(false);el<HTMLButtonElement>('saveProfile').disabled=true;el<HTMLButtonElement>('cancelProfile').disabled=true;el('dirtyState').textContent='已保存';draw();}
export function leaveEditor(){if(!dirty)return true;if(!confirm('动作组合尚未保存，是否放弃修改？'))return false;reset();return true;}
function reorder<T>(list:T[],index:number,delta:number){if(index+delta<0||index+delta>=list.length)return;[list[index],list[index+delta]]=[list[index+delta],list[index]];change();draw();}
function moreMenu(label:string,items:HTMLButtonElement[]){
 const menu=document.createElement('details');menu.className='row-menu';
 const summary=document.createElement('summary');summary.textContent='⋯';summary.setAttribute('aria-label',label);summary.title=label;
 menu.ontoggle=()=>{if(menu.open)for(const other of document.querySelectorAll<HTMLDetailsElement>('.row-menu[open]'))if(other!==menu)other.open=false;};
 const list=document.createElement('div');list.className='row-menu-items';list.append(...items);menu.append(summary,list);return menu;
}
function drawGroups(){
 const root=el('groups');root.replaceChildren();
 draft.groups.forEach((g,i)=>{
  const row=document.createElement('div');row.className='group-row'+(groupId===g.id?' selected':'');
  const title=document.createElement('input');title.type='text';title.value=g.name;title.maxLength=100;title.setAttribute('aria-label','组名称');title.onchange=()=>{g.name=title.value;change();drawEditor();};
  const enable=document.createElement('input');enable.type='checkbox';enable.className='switch';enable.checked=g.enabled;enable.setAttribute('aria-label',`启用 ${g.name}`);enable.onchange=()=>{g.enabled=enable.checked;change();};
  const head=document.createElement('div');head.className='group-row-head';head.append(title,enable);
  const choose=button(`${g.entries.length} 个条目 · ${groupId===g.id?'当前添加到此组':'选择此组'}`,()=>{groupId=g.id;drawGroups();});choose.className='group-select';
  const tools=moreMenu('管理 '+g.name,[button('上移',()=>reorder(draft.groups,i,-1)),button('下移',()=>reorder(draft.groups,i,1)),button('复制组',()=>{draft.groups.push({...structuredClone(g),id:uid(),name:g.name+' 副本',enabled:false});change();draw();}),button('删除组',()=>{draft.groups.splice(i,1);groupId=draft.groups[0]?.id||'';change();draw();})]);
  const foot=document.createElement('div');foot.className='group-row-foot';foot.append(choose,tools);row.append(head,foot);root.append(row);
 });
}
function drawEntries(){
 const root=el('entries');root.replaceChildren();
 draft.entries.forEach((e,i)=>{
  const row=document.createElement('div');row.className='entry-row'+(selected===e.id?' selected':'');
  const title=button('',()=>{selected=e.id;drawEntries();drawEditor();});title.className='entry-select';
  const name=document.createElement('span');name.textContent=e.name;const meta=document.createElement('small');meta.textContent=`${e.steps.length} 个步骤`;if(e.steps.some(s=>stepError(s,state.character!))){meta.textContent+=' · 包含缺失动作';meta.className='invalid';}title.append(name,meta);
  const tools=moreMenu('管理 '+e.name,[button('上移',()=>reorder(draft.entries,i,-1)),button('下移',()=>reorder(draft.entries,i,1)),button('复制条目',()=>{const copy={...structuredClone(e),id:uid(),name:e.name+' 副本'};draft.entries.push(copy);for(const g of draft.groups)if(g.entries.includes(e.id))g.entries.push(copy.id);selected=copy.id;change();draw();}),button('删除条目',()=>{draft.entries.splice(i,1);for(const g of draft.groups)g.entries=g.entries.filter(id=>id!==e.id);selected=draft.entries[Math.min(i,draft.entries.length-1)]?.id||'';change();draw();})]);
  row.append(title,tools);root.append(row);
 });
}
function addEntry(e:ActionEntry){draft.entries.push(e);draft.groups.find(g=>g.id===groupId)?.entries.push(e.id);selected=e.id;change();draw();}
function stepLabel(s:ActionStep){return s.kind==='action'?state.character?.actions?.find(a=>a.id===s.id)?.label:state.character?.furniture?.find(f=>f.id===s.id)?.name;}
function drawEditor(){
 const root=el('entryEditor');root.replaceChildren();const entry=draft.entries.find(e=>e.id===selected);
 if(!entry){const empty=document.createElement('div');empty.className='editor-empty';empty.textContent='从左侧选择一个条目，开始编排动作。';root.append(empty);return;}
 const heading=document.createElement('div');heading.className='editor-heading';const eyebrow=document.createElement('span');eyebrow.className='eyebrow';eyebrow.textContent='动作编排';
 const title=document.createElement('input');title.value=entry.name;title.maxLength=100;title.className='entry-title';title.setAttribute('aria-label','条目名称');title.onchange=()=>{entry.name=title.value;change();drawEntries();};
 const nameBlock=document.createElement('div');nameBlock.append(eyebrow,title);const preview=button('▷ 试播整个组合',()=>void send('preview',entry));preview.className='preview-entry';heading.append(nameBlock,preview);root.append(heading);
 const caption=document.createElement('div');caption.className='field-caption';caption.textContent='加入随机组';root.append(caption);
 const membership=document.createElement('div');membership.className='membership';
 for(const g of draft.groups){const label=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.checked=g.entries.includes(entry.id);check.onchange=()=>{g.entries=check.checked?[...new Set([...g.entries,entry.id])]:g.entries.filter(id=>id!==entry.id);change();drawGroups();};label.append(check,document.createTextNode(g.name));membership.append(label);}root.append(membership);
 const estimate=document.createElement('p');estimate.id='estimate';root.append(estimate);updateEstimate();
 entry.steps.forEach((s,i)=>{
  const card=document.createElement('div');card.className='step';const head=document.createElement('div');head.className='step-heading';const ordinal=document.createElement('span');ordinal.className='step-number';ordinal.textContent=String(i+1).padStart(2,'0');const kind=document.createElement('span');kind.className='step-kind';kind.textContent=s.kind==='furniture'?'家具动作':'普通动作';
  const tools=moreMenu(`管理第 ${i+1} 步`,[button('上移一步',()=>reorder(entry.steps,i,-1)),button('下移一步',()=>reorder(entry.steps,i,1)),button('删除此步',()=>{entry.steps.splice(i,1);change();drawEditor();})]);head.append(ordinal,kind,tools);card.append(head);
  const select=document.createElement('select');select.className='step-action';select.setAttribute('aria-label',`第 ${i+1} 步动作`);
  for(const [kind,items]of [['action',sortedActions()],['furniture',state.character?.furniture||[]]] as const){const group=document.createElement('optgroup');group.label=kind==='action'?'普通动作':'家具动作';for(const a of items)group.append(new Option('label'in a?a.label:a.name,kind+':'+a.id));select.append(group);}
  if(stepError(s,state.character!))select.append(new Option('缺失：'+s.id,s.kind+':'+s.id));select.value=s.kind+':'+s.id;select.onchange=()=>{const [kind,id]=select.value.split(':');s.kind=kind as ActionStep['kind'];s.id=id;change();drawEditor();};card.append(select);
  const fields=document.createElement('div');fields.className='step-fields';
  const mode=document.createElement('select');mode.append(new Option('播放次数','count'),new Option('循环秒数','seconds'));mode.value=s.mode;mode.onchange=()=>{s.mode=mode.value as ActionStep['mode'];s.value=s.mode==='count'?1:20;change();drawEditor();};const ml=document.createElement('label');ml.append(document.createTextNode('播放方式'),mode);fields.append(ml);
  const value=document.createElement('input');value.type='number';value.min=s.mode==='count'?'1':'.1';value.max=s.mode==='count'?'99':'3600';value.step=s.mode==='count'?'1':'.1';value.value=String(s.value);value.onchange=()=>{s.value=Number(value.value);change();updateEstimate();};
  const label=document.createElement('label');label.append(document.createTextNode(s.mode==='count'?'播放次数':'播放秒数'),value);fields.append(label);
  const gap=document.createElement('input');gap.type='number';gap.min='0';gap.max='3600';gap.step='.1';gap.value=String(s.gap);gap.onchange=()=>{s.gap=Number(gap.value);change();updateEstimate();};const gl=document.createElement('label');gl.append(document.createTextNode('结束后保持末帧（秒）'),gap);fields.append(gl);card.append(fields);
  const warning=stepError(s,state.character!);if(warning){const p=document.createElement('p');p.className='invalid';p.textContent=warning;card.append(p);}
  const tryStep=button('▷ 试播此步',()=>void send('preview',{id:'preview',name:entry.name,steps:[s]}));tryStep.className='try-step';card.append(tryStep);root.append(card);
 });
 const add=button('＋ 添加子动作',()=>{entry.steps.push({kind:'action',id:'interact',mode:'count',value:1,gap:0});change();drawEditor();});add.className='add-step';root.append(add);
}
function updateEstimate(){const e=draft?.entries.find(e=>e.id===selected),node=document.getElementById('estimate');if(!e||!node)return;const n=estimatedSeconds(e,state.durations,effectiveSpeed(state.settings).playback);node.textContent=n===undefined?'预计时长：部分动画将在首次加载后显示。':`预计 ${n.toFixed(1)} 秒（不含加载与场景切换）`;}
function drawBatch(){const root=el('batchActions');root.replaceChildren();const query=el<HTMLInputElement>('batchSearch').value.toLowerCase(),category=el<HTMLSelectElement>('batchCategory').value;for(const a of sortedActions()){if(category&&a.category!==category)continue;if(query&&!`${a.label} ${a.category} ${a.sourceName}`.toLowerCase().includes(query))continue;const label=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.dataset.actionId=a.id;label.append(check,document.createTextNode(a.label));root.append(label);}}
function draw(){drawGroups();drawEntries();drawEditor();drawBatch();}
function speedControls(){
 for(const [rootId,override]of [['globalSpeeds',false],['costumeSpeeds',true]] as const){const root=el(rootId);root.replaceChildren();for(const [key,label]of [['playback','动画播放'],['transition','动作过渡']] as const){
  const globalKey=key==='playback'?'playbackSpeed':'transitionSpeed',head=document.createElement('label');head.textContent=label;
  const check=document.createElement('input');check.type='checkbox';check.id='override-'+key;if(override){head.append(check);check.onchange=()=>{const all=structuredClone(state.settings.speedOverrides),current=all[state.settings.character]||{};if(check.checked)current[key]=state.settings[globalKey];else delete current[key];all[state.settings.character]=current;void send('settings',{speedOverrides:all});};}root.append(head);
  const row=document.createElement('div');row.className='speed-row';const slider=document.createElement('input'),number=document.createElement('input');slider.type='range';number.type='number';for(const input of [slider,number]){input.min='.25';input.max='4';input.step='.05';input.dataset.speed=key;input.dataset.override=String(override);input.setAttribute('aria-label',`${override?'当前服装':'全局'}${label}倍速`);input.onchange=()=>{const v=Number(input.value);if(!Number.isFinite(v)||v<.25||v>4)return;if(override){const all=structuredClone(state.settings.speedOverrides);all[state.settings.character]={...all[state.settings.character],[key]:v};void send('settings',{speedOverrides:all});}else void send('settings',{[globalKey]:v});};}slider.oninput=()=>number.value=slider.value;
  const reset=button('1×',()=>{number.value='1';number.dispatchEvent(new Event('change'));});reset.dataset.resetSpeed=key;reset.dataset.override=String(override);row.append(slider,number,reset);root.append(row);
 }}
}
export function setupSettings(command:typeof send,onDirty:(value:boolean)=>void){send=command;notifyDirty=onDirty;speedControls();
 window.addEventListener('keydown',e=>{if(e.key==='Escape'&&state?.range){e.preventDefault();void send('range-cancel');}});
 document.querySelectorAll<HTMLButtonElement>('nav [data-page]').forEach(b=>b.onclick=()=>{if(b.hasAttribute('aria-current')||!leaveEditor())return;for(const p of document.querySelectorAll<HTMLElement>('.page'))p.hidden=p.id!=='page-'+b.dataset.page;document.querySelectorAll('nav button').forEach(n=>n.removeAttribute('aria-current'));b.setAttribute('aria-current','page');});
 for(const key of ['theme','wheelPassThrough','outline','allowOffscreen','alwaysOnTop','size'])el<HTMLInputElement>(key).onchange=()=>{const input=el<HTMLInputElement>(key);void send('settings',{[key]:input.type==='checkbox'?input.checked:key==='size'?Number(input.value):input.value});};
 for(const id of ['outlineWidth','outlineWidthNumber']){const input=el<HTMLInputElement>(id);input.oninput=()=>{const value=Number(input.value);if(!Number.isFinite(value)||value<0||value>400)return;for(const other of ['outlineWidth','outlineWidthNumber'])if(other!==id)el<HTMLInputElement>(other).value=String(value);void send('settings',{outlineWidth:value});};}
 el('editRange').onclick=()=>void send('range-open');el<HTMLInputElement>('startup').onchange=()=>void send('startup',el<HTMLInputElement>('startup').checked);
 el('addGroup').onclick=()=>{const id=uid();draft.groups.push({id,name:'新动作组',enabled:false,entries:[]});groupId=id;change();draw();};
 el('addEntry').onclick=()=>addEntry({id:uid(),name:'新动作组合',steps:[{kind:'action',id:'interact',mode:'count',value:1,gap:0}]});
 el('saveProfile').onclick=async()=>{if(await send('profile-save',draft))reset();};el('cancelProfile').onclick=reset;
 el('batchSearch').oninput=drawBatch;el('batchCategory').onchange=drawBatch;el('batchAdd').onclick=()=>{const ids=[...el('batchActions').querySelectorAll<HTMLInputElement>('input:checked')].map(i=>i.dataset.actionId!);for(const id of ids){const action=state.character!.actions!.find(a=>a.id===id)!;let entry=draft.entries.find(e=>e.steps.length===1&&e.steps[0].kind==='action'&&e.steps[0].id===id);if(!entry){entry={id:uid(),name:action.label,steps:[{kind:'action',id,mode:'count',value:1,gap:0}]};draft.entries.push(entry);}const g=draft.groups.find(g=>g.id===groupId);if(g)g.entries=[...new Set([...g.entries,entry.id])];}change();draw();};
 window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='有未保存修改';}});
}
export function renderSettings(value:PanelState){state=value;if(draft&&lastActionSort!==state.settings.actionSort){drawEditor();drawBatch();}lastActionSort=state.settings.actionSort;document.documentElement.dataset.theme=state.settings.theme;el('runningStatus').textContent=state.playback?`${state.playback.entry} · 第 ${state.playback.index+1}/${state.playback.total} 步 · ${{loading:'加载中',playing:'播放中',gap:'间隔等待'}[state.playback.phase]}`:state.furniture?state.furniture.name:'准备就绪';
 if(characterId!==state.settings.character){characterId=state.settings.character;if(state.character)reset();}
 for(const key of ['theme','wheelPassThrough','outline','allowOffscreen','alwaysOnTop','size'] as const){const input=el<HTMLInputElement>(key);if(input.type==='checkbox')input.checked=state.settings[key] as boolean;else input.value=String(state.settings[key]);}el('sizeValue').textContent=state.settings.size+' px';
 for(const id of ['outlineWidth','outlineWidthNumber']){const input=el<HTMLInputElement>(id);if(document.activeElement!==input)input.value=String(state.settings.outlineWidth);input.disabled=!state.settings.outline;}
 for(const input of document.querySelectorAll<HTMLInputElement>('[data-speed]')){const key=input.dataset.speed as 'playback'|'transition',override=input.dataset.override==='true',o=state.settings.speedOverrides[characterId]?.[key];input.disabled=override&&o===undefined;input.value=String(override?(o??effectiveSpeed(state.settings)[key]):state.settings[key==='playback'?'playbackSpeed':'transitionSpeed']);}
 for(const key of ['playback','transition'] as const)el<HTMLInputElement>('override-'+key).checked=state.settings.speedOverrides[characterId]?.[key]!==undefined;
 for(const b of document.querySelectorAll<HTMLButtonElement>('[data-reset-speed]'))b.disabled=b.dataset.override==='true'&&state.settings.speedOverrides[characterId]?.[b.dataset.resetSpeed as 'playback'|'transition']===undefined;
 el<HTMLInputElement>('startup').checked=state.startup.enabled;el<HTMLInputElement>('startup').disabled=!state.startup.available;el('startupStatus').textContent=!state.startup.available?'开发／测试实例不修改系统启动项。':state.startup.enabled?'已启用：Windows 登录后显示桌宠。':state.startup.registered?'启动项已登记，但被 Windows 禁用。':'未启用开机启动。';updateEstimate();
}
