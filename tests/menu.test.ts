import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeSettings} from '../src/shared';
import {normalizeMenu,menuSections} from '../src/menu-config';
test('menu migration keeps every supported entry and mandatory recovery controls',()=>{
 const ids=menuSections.map(([id])=>id);assert.deepEqual(normalizeMenu(undefined),{order:ids,hidden:[]});
 const config=normalizeMenu({order:['quit','unknown','quit','actions'],hidden:['quit','open-panel','actions','actions','evil']});
 assert.deepEqual(config.order.slice(0,2),['quit','actions']);assert.equal(new Set(config.order).size,ids.length);assert.deepEqual(config.hidden,['actions']);
 assert.deepEqual(normalizeMenu({order:1,hidden:null}).order,ids);
});
test('all rotation axes survive multiple turns, negative turns, and JSON persistence',()=>{
 const settings=normalizeSettings({yaw:Math.PI*20,pitch:-Math.PI*13,roll:Math.PI*9});
 const restored=normalizeSettings(JSON.parse(JSON.stringify(settings)));for(const axis of ['pitch','yaw','roll'] as const)assert.equal(restored[axis],settings[axis]);
 const invalid=normalizeSettings({yaw:NaN,pitch:Infinity,roll:-Infinity});assert.deepEqual([invalid.pitch,invalid.yaw,invalid.roll],[0,0,0]);
 assert.equal(normalizeSettings({character:'hina',favorites:['hina:idle']}).roll,0);
});
