import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {attachLiquidReceiver} from '../src/liquid-receiver';

test('liquid receiving plane follows a lifted, tilted and scaled vessel',()=>{
 const root=new THREE.Group(),vessel=new THREE.Object3D();vessel.name='cup';root.add(vessel);
 const material=new THREE.MeshBasicMaterial();material.userData.BA_liquidReceiver={node:'cup',normal:[0,0,1],constant:-.052};
 const update=attachLiquidReceiver(material,root)!;
 const shader:any={uniforms:{},vertexShader:'#include <project_vertex>',fragmentShader:'#include <clipping_planes_fragment>'};material.onBeforeCompile(shader,{} as any);
 for(const lift of [0,.4,1]){
  vessel.position.set(.2,lift,-.1);vessel.rotation.set(.2,lift,.5);vessel.scale.setScalar(.85);update();
  const p=shader.uniforms.liquidPlane.value as THREE.Vector4;
  const distance=(z:number)=>{const point=vessel.localToWorld(new THREE.Vector3(0,0,z));return p.x*point.x+p.y*point.y+p.z*point.z+p.w;};
  assert.ok(distance(.08)>0);assert.ok(distance(-.04)<0);assert.ok(Math.abs(distance(.052))<1e-7);
 }
 material.dispose();
});

test('a missing receiving vessel fails explicitly instead of clipping against the origin',()=>{
 const material=new THREE.MeshBasicMaterial();material.userData.BA_liquidReceiver={node:'missing',normal:[0,0,1],constant:0};
 assert.throws(()=>attachLiquidReceiver(material,new THREE.Group()),/缺少水流接收容器/);material.dispose();
});
