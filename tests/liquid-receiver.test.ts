import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {attachLiquidReceiver} from '../src/liquid-receiver';
import {ModelOutline} from '../src/model-outline';

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

test('gated floor clip activates when prop rests on floor, releases when lifted, and propagates to outlines',()=>{
 const root=new THREE.Group(),floor=new THREE.Object3D(),box=new THREE.Object3D();
 floor.name='bone_root';box.name='bone_box_b_01';floor.rotation.x=-Math.PI/2;floor.add(box);root.add(floor);
 const material=new THREE.MeshBasicMaterial();
 material.userData.BA_liquidReceiver={node:'bone_root',normal:[0,0,1],constant:-.015,gate:{node:'bone_box_b_01',maxHeight:.025,fallbackConstant:.01}};
 const mesh=new THREE.Mesh(new THREE.BoxGeometry(.1,.1,.1),material);root.add(mesh);
 const update=attachLiquidReceiver(material,root)!;
 const outline=new ModelOutline(root);
 assert.equal(outline.meshes.length,1);
 const outlineMat=outline.meshes[0].material as THREE.ShaderMaterial;
 assert.equal(outlineMat.uniforms.clipPlane,material.userData._BA_clipPlane);
 box.position.set(0,0,.008);root.updateMatrixWorld(true);update();
 const p=material.userData._BA_clipPlane.value as THREE.Vector4;
 assert.ok(p.y*.02+p.w>0);assert.ok(p.y*.005+p.w<0);
 box.position.set(0,0,.05);root.updateMatrixWorld(true);update();
 assert.ok(p.y*.001+p.w>0);
 outline.dispose();mesh.geometry.dispose();material.dispose();
});
