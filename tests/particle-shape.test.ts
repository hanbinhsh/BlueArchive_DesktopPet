import test from 'node:test';
import assert from 'node:assert/strict';
import {particleShape} from '../src/cafe-particles';

const shape={enabled:true,type:16,m_Scale:{x:4,y:2,z:1},m_Position:{x:0,y:0,z:0},m_Rotation:{x:0,y:0,z:0}};
test('box-edge particles remain on two boundary planes',()=>{
 for(let seed=0;seed<100;seed++){
  const {position}=particleShape(shape,seed);
  const normalized=[position.x/4,position.y/2,position.z];
  assert.equal(normalized.filter(v=>Math.abs(v)===.5).length,2);
  assert.ok(normalized.every(v=>Math.abs(v)<=.5));
 }
});
test('random launch directions are normalized and deterministic',()=>{
 const s={...shape,randomDirectionAmount:1};
 const a=particleShape(s,42),b=particleShape(s,42),c=particleShape(s,43);
 assert.deepEqual(a.direction.toArray(),b.direction.toArray());assert.notDeepEqual(a.direction.toArray(),c.direction.toArray());
 assert.ok(Math.abs(a.direction.length()-1)<1e-12);
});
