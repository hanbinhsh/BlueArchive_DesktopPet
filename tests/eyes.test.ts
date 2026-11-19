import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {EyeFollower} from '../src/eyes';
test('pupil following is bounded, reversible and does not accumulate on unanimated bones',()=>{
 const root=new THREE.Group();root.position.set(2,3,1);root.scale.setScalar(2);
 const a=new THREE.Bone(),b=new THREE.Bone();a.name='Bip001_Xtra_eyeL';b.name='Bip001_Xtra_eyeR';a.position.x=-.1;b.position.x=.1;root.add(a,b);root.updateMatrixWorld(true);
 const camera=new THREE.PerspectiveCamera();camera.position.set(2,3,8);camera.lookAt(2,3,1);camera.updateMatrixWorld(true);
 const follower=new EyeFollower(root),base=a.position.clone();
 for(let i=0;i<200;i++){follower.reset();root.updateMatrixWorld(true);follower.update(true,{x:100000,y:-100000},400,400,camera,1/30);assert.ok(a.position.distanceTo(base)<.02);}
 assert.ok(follower.diagnostics().direction[0]>.9);follower.reset();assert.ok(a.position.distanceTo(base)<1e-9);
 follower.update(false,{x:0,y:0},400,400,camera,1/30);assert.deepEqual(follower.diagnostics().offsets,[]);
});
