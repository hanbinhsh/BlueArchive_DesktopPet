import {test} from 'node:test';
import assert from 'node:assert/strict';
import {sortActions,characterGroup} from '../src/library';
import {normalizeSettings} from '../src/shared';
const action=(id:string,label:string,category='剧情')=>({id,label,category,clip:id});
test('action categories, numeric variants and start-loop-end form a stable sequence',()=>{
 const input=[action('end','休息 · 结束'),action('ten','动作 10'),action('two','动作 2'),action('start','休息 · 开始'),action('ing','休息 · 持续'),action('idle','待机','常用')];
 const sorted=sortActions(input,new Set(),'category').map(a=>a.id);
 assert.equal(sorted[0],'idle');assert.ok(sorted.indexOf('two')<sorted.indexOf('ten'));assert.ok(sorted.indexOf('start')<sorted.indexOf('ing'));assert.ok(sorted.indexOf('ing')<sorted.indexOf('end'));assert.equal(input[0].id,'end');
});
test('favorites stay first; original order is recoverable without rewriting manifests',()=>{
 const input=[action('b','动作 10'),action('a','动作 2'),action('c','动作 1')];
 assert.deepEqual(sortActions(input,new Set(['a']),'source').map(a=>a.id),['a','b','c']);
 assert.deepEqual(sortActions(input,new Set(),'name').map(a=>a.id),['c','a','b']);
});
test('character favorites span outfits and migrate independently from action favorites',()=>{
 assert.equal(characterGroup('艾米 · 泳装'),'艾米');assert.equal(characterGroup('花子（泳装）'),'花子');
 const old=normalizeSettings({favorites:['eimi:idle']});assert.deepEqual(old.favoriteCharacters,[]);assert.equal(old.actionSort,'category');assert.deepEqual(old.favorites,['eimi:idle']);
 const s=normalizeSettings({favoriteCharacters:['艾米',' 艾米 ','','\n花子'],actionSort:'name'});assert.deepEqual(s.favoriteCharacters,['艾米']);assert.equal(s.actionSort,'name');
});
