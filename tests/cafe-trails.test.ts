import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {CafeTrail} from '../src/cafe-trails';
import {ParticleTransforms} from '../src/particle-transforms';

test('world-space trails seek deterministically, retain detached vertices, and expire',()=>{
 const root=new THREE.Group(),emitter=new THREE.Group();emitter.name='moving';root.add(emitter);
 const clip=new THREE.AnimationClip('scene',5,[new THREE.VectorKeyframeTrack('moving.position',[0,5],[0,0,0,5,0,0])]);
 const curve=(scalar:number)=>({minMaxState:0,scalar});
 const color={minMaxState:0,maxColor:{r:1,g:.5,b:.25,a:1}};
 const spec={clip:'scene',initialTime:0,burst:0,delay:curve(0),simulationSpeed:1,control:{start:0,duration:5,clipIn:0,speed:1},particle:{InitialModule:{startLifetime:curve(2)}},material:{queue:3000},renderer:{m_SortingOrder:0,m_ApplyActiveColorSpace:false}};
 const material=new THREE.MeshBasicMaterial({transparent:true});material.userData.BA_cafeTrail={spec,trail:{lifetime:curve(.25),widthOverTrail:curve(.1),colorOverTrail:color,colorOverLifetime:color,dieWithParticles:false},material:{colors:{_Color:[1,1,1,1]},floats:{_Multiply:1}}};
 const mesh=new THREE.Mesh(new THREE.BufferGeometry(),material);emitter.add(mesh);
 const trail=new CafeTrail(mesh,material,emitter,root,new ParticleTransforms(root,[clip])),camera=new THREE.PerspectiveCamera();camera.position.z=10;
 const snapshot=(t:number)=>{emitter.position.x=t;root.updateMatrixWorld(true);trail.update(t,'scene',camera);return Array.from(mesh.geometry.getAttribute('position').array);};
 const first=snapshot(1);assert.ok(mesh.geometry.drawRange.count>0);assert.ok(first.every(Number.isFinite));
 // The current emitter is x=1; retained source-world points span x=.5..1.
 const pos=mesh.geometry.getAttribute('position');assert.ok(Math.abs(pos.getX(0))<1e-6);assert.ok(Math.abs(pos.getX(60)+.5)<1e-6);
 snapshot(1.6);assert.deepEqual(snapshot(1),first,'Seeking cannot reuse stale frame history');
 snapshot(2.2);assert.equal(mesh.visible,true,'Trail survives particle death when authored');
 snapshot(2.6);assert.equal(mesh.visible,false);assert.equal(mesh.geometry.drawRange.count,0);
 trail.update(1,'other',camera);assert.equal(mesh.visible,false);mesh.geometry.dispose();material.dispose();
});
