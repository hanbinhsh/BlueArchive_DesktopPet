import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {CafeParticle} from '../src/cafe-particles';
test('velocity speed modifier scales launch speed as well as velocity-module motion',()=>{
 const c=(scalar:number)=>({minMaxState:0,scalar}),material=new THREE.MeshBasicMaterial();
 material.userData.BA_cafeParticle={clip:'test',control:{start:0,duration:4,speed:1,clipIn:0},burst:0,delay:c(0),material:{queue:3000,shader:'test',floats:{},colors:{}},particle:{InitialModule:{startLifetime:c(3),startSpeed:c(2),startSize:c(.1),startRotation:c(0),startColor:{minMaxState:0,maxColor:{r:1,g:1,b:1,a:1}}},VelocityModule:{enabled:true,x:c(0),y:c(0),z:c(2),speedModifier:c(.25)}}};
 const mesh=new THREE.Mesh(new THREE.PlaneGeometry(),material),root=new THREE.Group();root.add(mesh);const particle=new CafeParticle(mesh,material,new Set());particle.update(1,'test');assert.ok(Math.abs(mesh.position.z-1)<1e-6);particle.update(2,'test');particle.update(1,'test');assert.ok(Math.abs(mesh.position.z-1)<1e-6);mesh.geometry.dispose();material.dispose();
});

test('stretched billboards include the authored velocity contribution without losing direction',()=>{
 const c=(scalar:number)=>({minMaxState:0,scalar}),root=new THREE.Group(),camera=new THREE.PerspectiveCamera();camera.position.z=10;
 const material=new THREE.MeshBasicMaterial();material.userData.BA_cafeParticle={clip:'test',burst:0,delay:c(0),control:{start:0,duration:4,speed:1,clipIn:0},renderer:{m_RenderMode:1,m_LengthScale:2,m_VelocityScale:.2},material:{queue:3000,shader:'test',floats:{},colors:{}},particle:{InitialModule:{startLifetime:c(3),startSpeed:c(0),startSize:c(.5),startRotation:c(0),startColor:{minMaxState:0,maxColor:{r:1,g:1,b:1,a:1}}},VelocityModule:{enabled:true,x:c(2),y:c(0),z:c(0),speedModifier:c(1)}}};
 const mesh=new THREE.Mesh(new THREE.PlaneGeometry(),material);root.add(mesh);const particle=new CafeParticle(mesh,material,new Set());particle.update(1,'test',camera);
 root.updateMatrixWorld(true);
 const axis=mesh.localToWorld(new THREE.Vector3(.5,0,0)).sub(mesh.localToWorld(new THREE.Vector3(-.5,0,0)));
 assert.ok(Math.abs(axis.length()-1.4)<1e-6);assert.ok(axis.x<0&&Math.abs(axis.y)<1e-6);
 mesh.geometry.dispose();material.dispose();
});
