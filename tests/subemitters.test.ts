import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {CafeParticle,particleRandom} from '../src/cafe-particles';

test('death events use sampled lifetime, integrated position and the parent timeline clock',()=>{
 const c=(scalar:number)=>({minMaxState:0,scalar});
 const material=new THREE.MeshBasicMaterial(),mesh=new THREE.Mesh(new THREE.PlaneGeometry(),material),root=new THREE.Group();root.add(mesh);
 material.userData.BA_cafeParticle={clip:'test',seed:71,simulationSpeed:.5,burst:1,delay:c(.5),control:{start:3,duration:30,speed:2,clipIn:.25},material:{queue:3000,shader:'test',floats:{},colors:{}},particle:{InitialModule:{startLifetime:{minMaxState:3,minScalar:2,scalar:4},startSpeed:c(2),startSize:c(1),startRotation:c(0),startColor:{minMaxState:0,maxColor:{r:1,g:1,b:1,a:1}}}}};
 const particle=new CafeParticle(mesh,material,new Set());
 const life=2+2*particleRandom(71,'particle.InitialModule.startLifetime');
 const event=particle.emissionState(2);assert.ok(Math.abs(event.position.z-life*2)<1e-6);assert.equal(event.time,3+((1.5+life)/.5-.25)/2);
 particle.update(12,'test');assert.deepEqual(particle.emissionState(2).position.toArray(),event.position.toArray());
 const birth=particle.emissionState(0);assert.equal(birth.position.z,0);assert.equal(birth.time,3+(1.5/.5-.25)/2);
 particle.startAt(10);assert.equal(particle.emissionState(0).time,11.5);
 mesh.geometry.dispose();material.dispose();
});

test('birth inheritance multiplies color and size and preserves authored rotation',()=>{
 const c=(scalar:number)=>({minMaxState:0,scalar}),root=new THREE.Group();
 const make=(tint:number,size:number,rotation:number)=>{
  const material=new THREE.MeshBasicMaterial(),mesh=new THREE.Mesh(new THREE.PlaneGeometry(),material);root.add(mesh);
  material.userData.BA_cafeParticle={clip:'test',burst:0,delay:c(0),control:{start:0,duration:8,speed:1,clipIn:0},material:{queue:3000,shader:'test',floats:{},colors:{}},particle:{InitialModule:{startLifetime:c(2),startSpeed:c(0),startSize:c(size),startRotation:c(rotation),startColor:{minMaxState:0,maxColor:{r:tint,g:1,b:1,a:1}}}}};
  return {material,mesh,particle:new CafeParticle(mesh,material,new Set())};
 };
 const parent=make(.4,2,.2),child=make(.5,3,.3);child.particle.inheritFrom(parent.particle.emissionState(0),7);child.particle.update(.2,'test');
 assert.ok(Math.abs(child.material.color.r-.2)<1e-7);assert.equal(child.mesh.scale.x,6);assert.ok(Math.abs(child.mesh.rotation.z+.5)<1e-7);
 for(const item of [parent,child]){item.mesh.geometry.dispose();item.material.dispose();}
});
