import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {HaloFollower} from '../src/halo';
import {normalizeSettings} from '../src/shared';
test('halo follows animated head in translated/scaled parent and keeps lag bounded',()=>{
 const root=new THREE.Group();root.position.set(3,4,5);root.scale.setScalar(2);
 const head=new THREE.Object3D(),halo=new THREE.Object3D();root.add(head,halo);
 const follow=new HaloFollower(halo,head,{offset:[0,.4,0],rotation:[0,0,0,1],minOffset:[-.2,.2,-.2],maxOffset:[.2,.6,.2],positionPower:.1,rotationPower:.07,fixYRotation:false});
 follow.update(1/30,true);assert.ok(halo.position.distanceTo(new THREE.Vector3(0,.4,0))<1e-6);
 head.position.set(.5,.2,0);head.rotation.z=.3;follow.update(1/30);
 const relative=head.worldToLocal(halo.getWorldPosition(new THREE.Vector3()));
 assert.ok(relative.x>=-.200001&&relative.x<=.200001&&relative.y>=.199999&&relative.y<=.600001);
 for(let i=0;i<150;i++)follow.update(1/30);
 assert.ok(head.worldToLocal(halo.getWorldPosition(new THREE.Vector3())).distanceTo(new THREE.Vector3(0,.4,0))<1e-6);
 assert.ok(halo.quaternion.angleTo(head.quaternion)<1e-6);
});
test('old settings default to level pitch; full turns persist and invalid pitch resets',()=>{
 assert.equal(normalizeSettings({}).pitch,0);
 assert.equal(normalizeSettings({pitch:NaN}).pitch,0);
 assert.equal(normalizeSettings({pitch:100}).pitch,100);
 assert.equal(normalizeSettings({pitch:-100}).pitch,-100);
});
