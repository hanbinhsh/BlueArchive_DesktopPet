import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {attachWaterFx} from '../src/furniture-fx';
import {attachCafeSmoke} from '../src/cafe-smoke';

test('water materials with different authored UV switches compile distinct programs',async()=>{
 const keys=[];
 for(const flag of [0,1]){
  const m=new THREE.MeshBasicMaterial();m.userData.BA_waterFx={kind:'step',floats:{_Custom_Data_Main_Offset_Use:flag},color:[1,1,1,1]};
  await attachWaterFx(m,{},new Set());keys.push(m.customProgramCacheKey());m.dispose();
 }
 assert.notEqual(keys[0],keys[1]);
});

test('shared shader programs still receive each material’s own packed streams',async()=>{
 const keys=[],values=[];
 for(const streams of [[0,4,34,38],[0,4,5,34,38]]){
  const m=new THREE.MeshBasicMaterial(),textures=new Set<THREE.Texture>();
  m.userData.BA_smokeFx={kind:'step',floats:{},colors:{}};m.userData.BA_cafeParticle={renderer:{m_VertexStreams:streams}};
  m.userData.BA_customData=[[1,2,3,4],[5,6,7,8]];
  const update=await attachCafeSmoke(m,{},textures,{texture:{value:null},size:{value:new THREE.Vector2()},range:{value:new THREE.Vector2()},scale:{value:1},required:false});
  const shader={uniforms:{},vertexShader:'#include <uv_vertex>',fragmentShader:'#include <map_fragment>'} as any;m.onBeforeCompile(shader,{} as any);update!(0);values.push(shader.uniforms.cd1.value.toArray());
  keys.push(m.customProgramCacheKey());for(const t of textures)t.dispose();m.dispose();
 }
 assert.equal(keys[0],keys[1]);assert.deepEqual(values,[[3,4,5,6],[1,2,3,4]]);
});
