import {setupViewSettings,renderViewSettings} from './view-settings';
import {characterGroup,sortActions,compareActionNames} from './library';
import type { PanelApi, PanelState } from './shared';
import {setupSettings,renderSettings,leaveEditor} from './settings-panel';
declare global { interface Window { panel: PanelApi; } }
let state: PanelState;
let rosterKey = '';
let actionsKey = '';
let onlyFavoriteCharacters=false;
const api = window.panel;
const el = <T extends HTMLElement = HTMLElement>(id: string) => document.getElementById(id) as T;
async function command(name: string, value?: unknown) {
  if(name==='select'&&!leaveEditor())return false;
  try { render(await api.command(name, value));return true; }
  catch (e) { el('error').textContent = `操作失败：${String(e)}`;return false; }
}
function render(value: PanelState) {
  const positions=[...document.querySelectorAll<HTMLElement>('.page, #wardrobe')].map(e=>[e,e.scrollTop] as const);
  const aside = document.querySelector('aside')!;
  const scrollTop = aside.scrollTop;
  const pageX = window.scrollX, pageY = window.scrollY;
  state = value;
  el('current').textContent = state.character?.name || '角色未加载';
  el('characterNote').textContent = state.character?.note || '';
  el('error').textContent = state.error || '';
  for (const key of ['eyeFollow', 'randomIdle', 'roaming'] as const) el<HTMLInputElement>(key).checked = state.settings[key];
  for (const key of ['randomInterval', 'roamRadius', 'roamSpeed'] as const) {
    const select = el<HTMLSelectElement>(key), v = String(state.settings[key]);
    if (!Array.from(select.options).some(o => o.value === v)) select.add(new Option(v, v));
    select.value = v;
  }
  el('walkHint').textContent = state.character?.actions?.some(a => a.id === 'walk') ? '使用原版走路动画。' : '此角色没有可用的原版走路动画，将原地停留。';
  el<HTMLButtonElement>('testRandom').disabled = !state.ready;
  el<HTMLButtonElement>('testWalk').disabled = !state.ready || !state.character?.actions?.some(a=>a.id==='walk');
  el<HTMLSelectElement>('actionSort').value=state.settings.actionSort;
  renderRoster(); renderActions(); renderFurniture();renderSettings(state);renderViewSettings(state);
  // State replies and broadcasts can both render after one command. Preserve
  // the current viewport on each update, including favorite reordering.
  aside.scrollTop = scrollTop;
  window.scrollTo(pageX, pageY);
  for(const [e,top]of positions)e.scrollTop=top;
}
function renderRoster() {
  const root = el('roster');
  const query = el<HTMLInputElement>('search').value.trim();
  const key = JSON.stringify([query, state.characters, state.settings.favoriteCharacters,onlyFavoriteCharacters]);
  if (key === rosterKey) {
    root.querySelectorAll<HTMLButtonElement>('[data-character]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.character === state.settings.character)));
    return;
  }
  rosterKey = key; root.replaceChildren();
  const groups = new Map<string, PanelState['characters']>();
  el('allCharacters').setAttribute('aria-pressed',String(!onlyFavoriteCharacters));el('favoriteCharacters').setAttribute('aria-pressed',String(onlyFavoriteCharacters));
  el('favoriteCharacters').textContent=`角色收藏夹 · ${state.settings.favoriteCharacters.length}`;
  for (const item of state.characters.filter(c => c.name.includes(query)&&(!onlyFavoriteCharacters||state.settings.favoriteCharacters.includes(characterGroup(c.name))))) {
    const group = characterGroup(item.name);
    if (!groups.has(group)) groups.set(group, []); groups.get(group)!.push(item);
  }
  for (const [name, items] of groups) {
    const heading = document.createElement('h3'); heading.textContent = name;
    const header=document.createElement('div');header.className='roster-heading';
    const star=document.createElement('button');star.className='star';star.dataset.characterFavorite=items[0].id;const favorite=state.settings.favoriteCharacters.includes(name);drawStar(star);star.setAttribute('aria-label',`${favorite?'取消收藏':'收藏角色'}${name}`);star.setAttribute('aria-pressed',String(favorite));star.onclick=()=>{void command('favorite-character',items[0].id);};header.append(heading,star);root.append(header);
    const grid = document.createElement('div'); grid.className = 'grid'; root.append(grid);
    for (const item of items) {
      const button = document.createElement('button'); button.className = 'card'; button.dataset.character = item.id;
      button.setAttribute('aria-pressed', String(item.id === state.settings.character)); button.setAttribute('aria-label', item.name);
      if (item.thumbnail) { const image = document.createElement('img'); image.src = item.thumbnail; image.alt = ''; button.append(image); }
      else { const missing = document.createElement('span'); missing.className = 'missing'; missing.textContent = '暂无预览'; button.append(missing); }
      const label = document.createElement('span'); label.textContent = item.name.replace(name, '').replace(/^\s*·\s*/, '') || name; button.append(label);
      button.onclick = () => { el('notice').textContent = `正在切换至 ${item.name}`; void command('select', item.id); }; grid.append(button);
    }
  }
  el('count').textContent=`${groups.size} 位角色 · ${[...groups.values()].reduce((n,items)=>n+items.length,0)} 套服装`;
  if (!groups.size) root.textContent = onlyFavoriteCharacters?'收藏夹中没有匹配的角色。点击角色名称旁的 ☆，即可收藏她的全部服装。':'没有找到匹配的角色或服装。';
}
function renderActions() {
  const root = el('actions');
  const only = el<HTMLInputElement>('onlyFavorites').checked;
  const category = el<HTMLSelectElement>('actionCategory').value;
  const query = el<HTMLInputElement>('actionSearch').value.trim().toLowerCase();
  const actions = [...(state.character?.actions || [])];
  const key = JSON.stringify([state.settings.character, actions, state.settings.favorites, state.settings.actionSort, only, category, query]);
  if (key === actionsKey) {
    root.querySelectorAll<HTMLButtonElement>('[data-action]').forEach(button => { button.disabled = !state.ready; });
    return;
  }
  actionsKey = key;
  const content = document.createDocumentFragment();
  const favorite = (id: string) => state.settings.favorites.includes(`${state.settings.character}:${id}`);
  const sorted=sortActions(actions,new Set(actions.filter(a=>favorite(a.id)).map(a=>a.id)),state.settings.actionSort);
  for (const action of sorted) {
    if (only && !favorite(action.id)) continue;
    if (category && (action.category || '常用') !== category) continue;
    if (query && !`${action.label} ${action.sourceName || ''}`.toLowerCase().includes(query)) continue;
    const row = document.createElement('div'); row.className = 'action';
    const play = document.createElement('button'); play.className = 'play'; play.dataset.action = action.id; play.textContent = `▷  ${action.label}`; play.disabled = !state.ready;
    if (action.sourceName) play.title = action.sourceName;
    play.onclick = () => { el('notice').textContent = `正在桌宠上试播：${action.label}`; void command('action', action.id); };
    const star = document.createElement('button'); star.className = 'star'; star.dataset.favorite = action.id;
    drawStar(star); star.setAttribute('aria-label', `收藏${action.label}`); star.setAttribute('aria-pressed', String(favorite(action.id)));
    star.onclick = () => { void command('favorite', action.id); }; row.append(play, star); content.append(row);
  }
  root.replaceChildren(content);
  el('actionCount').textContent = `显示 ${root.children.length} / ${actions.length} 个动作`;
  if (!root.children.length) root.textContent = '没有匹配的动作，请调整分类、搜索或收藏筛选。';
}
function renderFurniture() {
  const root = el('furniture');
  const content = document.createDocumentFragment();
  el('furnitureHint').textContent = state.furniture ? `正在播放：${state.furniture.name}。拖动移动整组场景，单击从头播放。自动活动暂停。` : state.character?.furniture?.length ? '选择家具，循环播放对应的原版互动动作。' : '当前服装暂无已适配的家具互动。';
  for (const item of [...(state.character?.furniture || [])].sort((a,b)=>state.settings.actionSort==='source'?0:compareActionNames(a.name,b.name))) {
    const row = document.createElement('div'); row.className = 'action';
    const button = document.createElement('button'); button.className = 'play'; button.dataset.furniture = item.id; button.textContent = item.name;
    button.disabled = !state.ready; button.setAttribute('aria-pressed', String(state.furniture?.id === item.id));
    button.onclick = () => { void command('furniture', item.id); }; row.append(button); content.append(row);
    if (item.note) { const note = document.createElement('p'); note.textContent = item.note; content.append(note); }
  }
  root.replaceChildren(content);
  el<HTMLButtonElement>('closeFurniture').disabled = !state.furniture || (!state.ready && !state.error);
}
el('closeFurniture').onclick = () => { void command('furniture', ''); };
el('search').addEventListener('input', renderRoster);
el('allCharacters').onclick=()=>{onlyFavoriteCharacters=false;renderRoster();};
el('favoriteCharacters').onclick=()=>{onlyFavoriteCharacters=true;renderRoster();};
el('actionSort').onchange=()=>{void command('settings',{actionSort:el<HTMLSelectElement>('actionSort').value});};
el('onlyFavorites').addEventListener('change', renderActions);
el('actionCategory').addEventListener('change', renderActions);
el('actionSearch').addEventListener('input', renderActions);
el('recover').onclick = () => { void command('recover'); };
for (const key of ['eyeFollow', 'randomIdle', 'randomInterval', 'roaming', 'roamRadius', 'roamSpeed']) {
  el(key).addEventListener('change', () => { void command('settings', {
    eyeFollow: el<HTMLInputElement>('eyeFollow').checked, randomIdle: el<HTMLInputElement>('randomIdle').checked, randomInterval: Number(el<HTMLSelectElement>('randomInterval').value),
    roaming: el<HTMLInputElement>('roaming').checked, roamRadius: Number(el<HTMLSelectElement>('roamRadius').value), roamSpeed: Number(el<HTMLSelectElement>('roamSpeed').value)
  }); });
}
for (const [button, action, label] of [['testRandom','test-random','随机动作'],['testWalk','test-walk','走动'],['stopTest','stop-test','停止']] as const) {
 el(button).onclick = () => { el('notice').textContent = `测试：${label}`; void command(action); };
}
setupSettings(command,value=>api.dirty(value));
setupViewSettings(command);
api.onState(render);
void api.state().then(render).catch(e => { el('error').textContent = String(e); });

function drawStar(button:HTMLButtonElement){const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('aria-hidden','true');const path=document.createElementNS(svg.namespaceURI,'path');path.setAttribute('d','M12 3 14.8 8.8 21.2 9.7 16.6 14.2 17.7 20.6 12 17.6 6.3 20.6 7.4 14.2 2.8 9.7 9.2 8.8Z');svg.append(path);button.append(svg);}
