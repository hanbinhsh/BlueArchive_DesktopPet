import test from 'node:test';
import assert from 'node:assert/strict';
import * as T from 'three';
import {CafeParticle} from '../src/cafe-particles';

// Ground truth: test-results/unity036-pivot.txt, baked by Unity itself.
function depth(alignment:number,pivot:number,yaw:number){
 const c=(scalar:number)=>({minMaxState:0,scalar});
 const root=new T.Group(),emitter=new T.Group();root.add(emitter);root.rotation.y=yaw;
 const material=new T.MeshBasicMaterial();
 material.userData.BA_cafeParticle={clip:'probe',control:{start:0,duration:2,speed:1,clipIn:0},delay:c(0),burst:0,
  material:{shader:'probe',queue:3000,colors:{},floats:{}},renderer:{m_RenderMode:0,m_RenderAlignment:alignment},
  particle:{InitialModule:{startLifetime:c(2),startSpeed:c(0),gravityModifier:c(0),startSize:c(1),startRotation:c(0),startColor:{minMaxState:0,maxColor:{r:1,g:1,b:1,a:1}}}}};
 const geometry=new T.PlaneGeometry();geometry.translate(0,0,pivot);const mesh=new T.Mesh(geometry,material);emitter.add(mesh);
 const camera=new T.OrthographicCamera(-2,2,2,-2,.1,100);camera.position.z=10;camera.lookAt(0,0,0);camera.updateMatrixWorld(true);root.updateMatrixWorld(true);
 new CafeParticle(mesh,material,new Set(),root).update(.1,'probe',camera);root.updateMatrixWorld(true);
 const center=mesh.localToWorld(new T.Vector3(0,0,pivot));geometry.dispose();material.dispose();return center.z;
}
test('View negative depth pivot recedes, Facing negative pivot approaches, as in Unity',()=>{
 for(const yaw of [0,.7,2.1]){
  assert.ok(Math.abs(depth(0,-.2,yaw)+.2)<1e-6);
  assert.ok(Math.abs(depth(3,-.2,yaw)-.2)<1e-6);
  assert.ok(Math.abs(depth(0,.2,yaw)-.2)<1e-6);
 }
});
