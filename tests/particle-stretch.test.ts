import test from 'node:test';
import assert from 'node:assert/strict';
import * as T from 'three';
import {CafeParticle} from '../src/cafe-particles';

function sprite(flip=0,length=2,depthFactor=0){
 const c=(scalar:number)=>({minMaxState:0,scalar});
 const root=new T.Group(),emitter=new T.Group();root.add(emitter);emitter.rotation.y=Math.PI/2;
 const material=new T.MeshBasicMaterial();
 material.userData.BA_cafeParticle={clip:'test',control:{start:0,duration:3,speed:1,clipIn:0},delay:c(0),burst:0,material:{shader:'test',queue:3000,colors:{},floats:{}},renderer:{m_RenderMode:1,m_RenderAlignment:2,m_LengthScale:length,m_VelocityScale:0,m_Flip:{x:flip,y:0,z:0}},particle:{InitialModule:{startLifetime:c(2),startSpeed:c(1),gravityModifier:c(0),size3D:true,startSize:c(2),startSizeY:c(3),startSizeZ:c(1),startRotation:c(0),startColor:{minMaxState:0,maxColor:{r:1,g:1,b:1,a:1}}}}};
 const mesh=new T.Mesh(new T.PlaneGeometry(),material);emitter.add(mesh);root.updateMatrixWorld(true);
 material.userData.BA_cafeParticle.material.floats._ZOffsetFactor=depthFactor;
 const camera=new T.OrthographicCamera(-10,10,10,-10,.1,100);camera.position.z=10;camera.lookAt(0,0,0);camera.updateMatrixWorld(true);
 const particle=new CafeParticle(mesh,material,new Set(),root);
 particle.update(.5,'test',camera);root.updateMatrixWorld(true);
 const along=mesh.localToWorld(new T.Vector3(.5,0,0)).sub(mesh.localToWorld(new T.Vector3(-.5,0,0)));
 const across=mesh.localToWorld(new T.Vector3(0,.5,0)).sub(mesh.localToWorld(new T.Vector3(0,-.5,0)));
 const depth={enabled:material.polygonOffset,factor:material.polygonOffsetFactor,units:material.polygonOffsetUnits};
 mesh.geometry.dispose();material.dispose();return {along,across,tip:mesh.localToWorld(new T.Vector3(.5,0,0)),depth};
}
test('stretched texture U follows motion and retains the authored length/width',()=>{
 const {along,across}=sprite();assert.ok(along.x>5.99);assert.ok(Math.abs(along.y)<1e-6);
 assert.ok(Math.abs(across.length()-2)<1e-6);assert.ok(Math.abs(along.dot(across))<1e-6);
});
test('authored U flip turns the sigh tail back toward its emission point',()=>{
 assert.ok(sprite(1).along.x<0);assert.ok(sprite(0,-2).along.x<0);
});

test("native Unity zero-pivot stretched sprites anchor U=0 at the particle",()=>{
 const {tip}=sprite();assert.ok(Math.abs(tip.x-.5)<1e-6);
});
test('authored foam slope bias survives particle material setup',()=>{
 assert.deepEqual(sprite(0,2,-20).depth,{enabled:true,factor:-20,units:0});
 assert.deepEqual(sprite().depth,{enabled:false,factor:0,units:0});
});
