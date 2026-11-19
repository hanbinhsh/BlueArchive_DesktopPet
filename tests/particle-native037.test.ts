import test from 'node:test';
import assert from 'node:assert/strict';
import * as T from 'three';
import {CafeParticle,unityCurve} from '../src/cafe-particles';

test('Unity serialized curve infinity modes repeat or ping-pong short curves',()=>{
 const keys=[{time:0,value:0,inSlope:2.5,outSlope:2.5},{time:.4,value:1,inSlope:2.5,outSlope:2.5}];
 const c=(mode:number)=>({minMaxState:1,scalar:1,maxCurve:{m_Curve:keys,m_PreInfinity:mode,m_PostInfinity:mode}});
 assert.ok(Math.abs(unityCurve(c(1),.6)-.5)<1e-6);
 assert.ok(Math.abs(unityCurve(c(0),.9)-.25)<1e-6);
 assert.equal(unityCurve(c(2),.9),1);
});
test('Hidden Unity renderers still deliver death events and remain invisible',()=>{
 const c=(scalar:number)=>({minMaxState:0,scalar});
 const material=new T.MeshBasicMaterial(),mesh=new T.Mesh(new T.PlaneGeometry(),material);
 material.userData.BA_cafeParticle={clip:'test',burst:0,delay:c(0),control:{start:0,duration:5,speed:1,clipIn:0},renderer:{m_Enabled:false},material:{queue:3000,shader:'test',floats:{},colors:{}},particle:{InitialModule:{startLifetime:c(2),startSpeed:c(3),startSize:c(1),startRotation:c(0),startColor:{minMaxState:0,maxColor:{r:1,g:1,b:1,a:1}}}}};
 const p=new CafeParticle(mesh,material,new Set());p.update(.5,'test');assert.equal(mesh.visible,false);assert.ok(Math.abs(p.emissionState(2).position.z-6)<1e-8);
 mesh.geometry.dispose();material.dispose();
});
test('Two curves retain independent wrapping when their key ranges differ',()=>{
 const linear=(end:number,wrap:number)=>({m_Curve:[{time:0,value:0,inSlope:1/end,outSlope:1/end},{time:end,value:1,inSlope:1/end,outSlope:1/end}],m_PostInfinity:wrap});
 assert.ok(Math.abs(unityCurve({minMaxState:2,minScalar:1,scalar:1,minCurve:linear(.2,1),maxCurve:linear(1,2)},.9,.5)-.7)<1e-6);
});
