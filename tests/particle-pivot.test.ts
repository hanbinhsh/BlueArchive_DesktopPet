import test from 'node:test';
import assert from 'node:assert/strict';
import * as T from 'three';
import {CafeParticle} from '../src/cafe-particles';

function at(flip:number,mode=0,pivot=.25,rotation=Math.PI,point?:T.Vector3){
 const c=(scalar:number)=>({minMaxState:0,scalar}),material=new T.MeshBasicMaterial(),geometry=new T.PlaneGeometry(1,1);geometry.translate(0,pivot,0);
 const root=new T.Group(),emitter=new T.Group(),mesh=new T.Mesh(geometry,material);root.add(emitter);emitter.add(mesh);emitter.rotation.y=Math.PI/2;
 material.userData.BA_cafeParticle={clip:'test',burst:0,delay:c(0),control:{start:0,duration:3,speed:1,clipIn:0},renderer:{m_RenderMode:mode,m_RenderAlignment:0,m_LengthScale:2,m_Flip:{x:flip,y:flip,z:0}},material:{shader:'test',colors:{},floats:{}},particle:{InitialModule:{startLifetime:c(2),startSpeed:c(1),startSize:c(1),startRotation:c(rotation),startColor:{minMaxState:0,maxColor:{r:1,g:1,b:1,a:1}}}}};
 const camera=new T.Camera();camera.updateMatrixWorld(true);root.updateMatrixWorld(true);const p=new CafeParticle(mesh,material,new Set());p.update(.5,'test',camera);root.updateMatrixWorld(true);
 const center=mesh.localToWorld(point||new T.Vector3(0,pivot,0));geometry.dispose();material.dispose();return center;
}
test('double-flipped credit sprites retain their authored pivot centre',()=>{assert.ok(at(0).distanceTo(at(1))<1e-6);});
test('positive source billboard roll rotates the reflected texture clockwise',()=>{
 const marker=at(0,0,0,Math.PI/2,new T.Vector3(-.5,0,0)),center=at(0,0,0,Math.PI/2);const delta=marker.sub(center);assert.ok(Math.abs(delta.x)<1e-6);assert.ok(delta.y<-.4999);
});
test('stretched Y pivot offsets the jet along motion rather than across it',()=>{
 const delta=at(0,1,1).sub(at(0,1,0));assert.ok(Math.abs(delta.x-2)<1e-6);assert.ok(Math.abs(delta.y)<1e-6);assert.ok(at(0,1,1).distanceTo(at(1,1,1))<1e-6);
});
