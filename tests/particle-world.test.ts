import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {CafeParticle} from '../src/cafe-particles';
import {ParticleTransforms} from '../src/particle-transforms';

function setup(space:number,birth=0){
 const c=(scalar:number)=>({minMaxState:0,scalar}),root=new THREE.Group(),emitter=new THREE.Group();emitter.name='hose';root.add(emitter);
 const clip=new THREE.AnimationClip('pour',3,[new THREE.QuaternionKeyframeTrack('hose.quaternion',[0,3],[0,0,1,0,0,0,1,0]),new THREE.VectorKeyframeTrack('hose.position',[0,1,3],[2,3,0,5,10,0,5,10,0])]);
 const material=new THREE.MeshBasicMaterial();material.userData.BA_cafeParticle={clip:'pour',simulationSpace:space,control:{start:0,duration:3,speed:1,clipIn:0},burst:birth,delay:c(0),material:{queue:3000,shader:'test',floats:{},colors:{}},particle:{InitialModule:{startLifetime:c(2),startSpeed:c(0),gravityModifier:c(1),startSize:c(.1),startRotation:c(0),startColor:{minMaxState:0,maxColor:{r:1,g:1,b:1,a:1}}}}};
 const mesh=new THREE.Mesh(new THREE.PlaneGeometry(),material);emitter.add(mesh);
 const transforms=new ParticleTransforms(root,[clip]),particle=new CafeParticle(mesh,material,new Set(),root,transforms),mixer=new THREE.AnimationMixer(root);mixer.clipAction(clip).play();
 const at=(time:number)=>{mixer.setTime(time);root.updateMatrixWorld(true);particle.update(time,'pour');root.updateMatrixWorld(true);return mesh.getWorldPosition(new THREE.Vector3());};
 return {root,emitter,mesh,material,at,transforms,particle};
}

test('world droplets keep their launch point and fall down after the hose moves',()=>{
 const s=setup(1);const position=s.at(1);
 assert.ok(Math.abs(position.x-2)<1e-6);assert.ok(Math.abs(position.y-(3-9.8100004196167/2))<1e-5);
 s.at(1.8);assert.ok(s.at(1).distanceTo(position)<1e-6);
 // Changing desktop framing does not change source-world simulation.
 s.root.scale.setScalar(.4);s.root.rotation.z=.6;s.root.position.set(8,-4,2);
 const framed=s.at(1);assert.ok(framed.distanceTo(s.root.localToWorld(position.clone()))<1e-6);
 s.mesh.geometry.dispose();s.material.dispose();
});

test('later droplets sample the hose at their own birth time, not the bind pose',()=>{
 const s=setup(1,1),position=s.at(1.5);
 assert.ok(Math.abs(position.x-5)<1e-6);assert.ok(Math.abs(position.y-(10-9.8100004196167*.5*.5/2))<1e-5);
 s.mesh.geometry.dispose();s.material.dispose();
});

test('local particles use animated gravity orientation and still follow their emitter',()=>{
 const s=setup(0),position=s.at(1);
 assert.ok(Math.abs(position.x-5)<1e-6);assert.ok(Math.abs(position.y-(10-9.8100004196167/2))<1e-5);
 s.mesh.geometry.dispose();s.material.dispose();
});
