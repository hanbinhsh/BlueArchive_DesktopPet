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

test('gated floor clip with followOffset tracks box hop height and releases above maxHeight',()=>{
 const root=new THREE.Group(),floor=new THREE.Object3D(),box=new THREE.Object3D();
 floor.name='bone_root';box.name='bone_box_b_01';floor.rotation.x=-Math.PI/2;floor.add(box);root.add(floor);
 const material=new THREE.MeshBasicMaterial();
 material.userData.BA_liquidReceiver={node:'bone_root',normal:[0,0,1],constant:-.015,gate:{node:'bone_box_b_01',maxHeight:.05,fallbackConstant:.01,followOffset:.075}};
 const update=attachLiquidReceiver(material,root)!;
 const p=material.userData._BA_clipPlane.value as THREE.Vector4;
 // Rest pose (box at -0.056): clips below 0.019
 box.position.set(0,0,-.056);root.updateMatrixWorld(true);update();
 assert.ok(p.y*.025+p.w>0);assert.ok(p.y*.010+p.w<0);
 // Hop peak during interact (box at +0.017): tracks up to 0.092 so skirt never peeks below box
 box.position.set(0,0,.017);root.updateMatrixWorld(true);update();
 assert.ok(p.y*.10+p.w>0);assert.ok(p.y*.08+p.w<0);
 // Walk lift (box at +0.22 >= maxHeight): releases to fallbackConstant (+0.01) so legs show
 box.position.set(0,0,.22);root.updateMatrixWorld(true);update();
 assert.ok(p.y*.001+p.w>0);
 material.dispose();
});

test('gated floor clip releases when box is tipped on its side, shrunk away, or offset from target',()=>{
 const root=new THREE.Group(),floor=new THREE.Object3D(),boxMain=new THREE.Object3D(),boxBottom=new THREE.Object3D(),bip=new THREE.Object3D();
 floor.name='bone_root';boxMain.name='bone_box_main';boxBottom.name='bone_box_b_01';bip.name='Bip001';
 floor.rotation.x=-Math.PI/2;floor.add(boxMain);boxMain.add(boxBottom);floor.add(bip);root.add(floor);
 boxBottom.position.set(0,0,-.38);
 const material=new THREE.MeshBasicMaterial();
 material.userData.BA_liquidReceiver={
  node:'bone_root',normal:[0,0,1],constant:-.015,
  gate:{node:'bone_box_b_01',maxHeight:.14,fallbackConstant:10,followOffset:.085,alignNode:'bone_box_main',minScale:.3,minUpDot:.9,targetNode:'Bip001',maxLateral:.4},
 };
 const update=attachLiquidReceiver(material,root)!;
 const p=material.userData._BA_clipPlane.value as THREE.Vector4;
 // Upright box hopping to h=+0.08 (< 0.14): clips at 0.08 + 0.085 = 0.165
 boxMain.position.set(0,0,.396);boxMain.rotation.set(0,0,0);boxMain.scale.setScalar(.8311);bip.position.set(0,0,.2);
 root.updateMatrixWorld(true);update();
 assert.ok(p.y*.18+p.w>0);assert.ok(p.y*.12+p.w<0);
 // Tipped 90 deg on its side (Tactical_Start / Exs): upDot=0 < 0.9 -> releases to fallbackConstant (10)
 boxMain.position.set(0,0,.40);boxMain.rotation.set(Math.PI/2,0,0);boxMain.scale.setScalar(.9);
 root.updateMatrixWorld(true);update();
 assert.ok(p.y*-.5+p.w>0);
 // Shrunk away (ST_Death / Formation_Idle): scale=0.01 < 0.3 -> releases
 boxMain.position.set(0,0,.05);boxMain.rotation.set(0,0,0);boxMain.scale.setScalar(.01);
 root.updateMatrixWorld(true);update();
 assert.ok(p.y*-.5+p.w>0);
 // Box parked 1m away from character (Exs_Cutin_Genryumon): lateral=1.0 > 0.4 -> releases
 boxMain.position.set(-1,0,.40);boxMain.rotation.set(0,0,0);boxMain.scale.setScalar(1);
 root.updateMatrixWorld(true);update();
 assert.ok(p.y*-.5+p.w>0);
 // Both box and character hopped together to y=+1.77 (Exs upright ending): lateral=0 <= 0.4 -> clips!
 boxMain.position.set(0,1.77,.35);bip.position.set(0,1.77,.2);boxMain.scale.setScalar(.872);
 root.updateMatrixWorld(true);update();
 assert.ok(p.y*.05+p.w<0);
 material.dispose();
});
