import test from 'node:test';
import assert from 'node:assert/strict';
import * as T from 'three';
import {CafeParticle} from '../src/cafe-particles';

function emitted(burst:number,period=1.4){
 const c=(scalar:number)=>({minMaxState:0,scalar}),ramp={minMaxState:1,scalar:7,maxCurve:{m_Curve:[{time:0,value:0,outSlope:1},{time:1,value:1,inSlope:1}]}};
 const material=new T.MeshBasicMaterial(),root=new T.Group(),mesh=new T.Mesh(new T.PlaneGeometry(),material);root.add(mesh);
 material.userData.BA_cafeParticle={clip:'notes',control:{start:0,duration:10,speed:1,clipIn:0},burst,period,delay:c(0),renderer:{m_RenderMode:0,m_RenderAlignment:2},material:{shader:'test',colors:{},floats:{}},particle:{InitialModule:{startLifetime:c(.2),startSpeed:ramp,startSize:c(1),startRotation:c(0),startColor:{minMaxState:0,maxColor:{r:1,g:1,b:1,a:1}}}}};
 const p=new CafeParticle(mesh,material,new Set(),root),death=p.emissionState(2);mesh.geometry.dispose();material.dispose();return death.position.z;
}
test('later Airi note emitters travel according to the initial-speed curve',()=>{
 assert.ok(Math.abs(emitted(0))<1e-6);assert.ok(Math.abs(emitted(.7)-.7)<1e-6);assert.ok(Math.abs(emitted(1.05)-1.05)<1e-6);
});
test('initial curves repeat with emitter cycles including prewarm births',()=>{
 assert.ok(Math.abs(emitted(2.1)-emitted(.7))<1e-6);assert.ok(Math.abs(emitted(-.7)-emitted(.7))<1e-6);
});
