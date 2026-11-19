import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {CafeParticle,particleAge,particleShape,particleRandom,unityCurve} from '../src/cafe-particles';
test('ring buffers preserve a water surface past its six second particle lifetime',()=>{
 assert.equal(particleAge(26,6,2),2);
 assert.ok(particleAge(26,6,1)<6);
 assert.equal(particleAge(26,6,0),26);
 assert.equal(particleAge(-1,6,2),-1);
 assert.equal(particleAge(5,8,2,{x:.25,y:.5}),3);
});
test('two-constant and two-curve samples preserve a particle-specific random factor',()=>{
 assert.equal(unityCurve({minMaxState:3,minScalar:2,scalar:6},0,.25),3);
 const keys=(value:number)=>({m_Curve:[{time:0,value,outSlope:0},{time:1,value,inSlope:0}]});
 assert.equal(unityCurve({minMaxState:2,minScalar:1,scalar:1,minCurve:keys(2),maxCurve:keys(6)},.7,.25),3);
 assert.equal(particleRandom(51,'size'),particleRandom(51,'size'));assert.notEqual(particleRandom(51,'size'),particleRandom(51,'lifetime'));
});
test('circle burst spreads three knock rays and box shape respects source rotation',()=>{
 const shape={enabled:true,type:10,radiusThickness:0,radius:{value:2},arc:{value:90,mode:3},m_Position:{x:0,y:0,z:0},m_Rotation:{x:0,y:0,z:0},m_Scale:{x:1,y:1,z:1}};
 const a=particleShape(shape,51,0,3),b=particleShape(shape,51,2,3);assert.ok(Math.abs(a.position.length()-2)<1e-9);assert.ok(Math.abs(a.direction.angleTo(b.direction)-Math.PI/3)<1e-9);
 const box=particleShape({...shape,type:5,m_Rotation:{x:0,y:90,z:0},m_Scale:{x:.2,y:1.5,z:1}},10);assert.ok(Math.abs(box.position.x)<=.5&&Math.abs(box.position.y)<=.75&&Math.abs(box.position.z)<=.1);
});
test('absolute particle evaluation survives seeking and does not accumulate motion',()=>{
 const c=(scalar:number)=>({minMaxState:0,scalar});const material=new THREE.MeshBasicMaterial();material.userData.BA_cafeParticle={clip:'test',control:{start:0,duration:10,speed:1,clipIn:0},seed:51,burst:0,delay:c(0),material:{queue:3000,shader:'test',floats:{},colors:{}},particle:{InitialModule:{startLifetime:c(2),startSpeed:c(1),startSize:c(.2),startRotation:c(0),startColor:{minMaxState:0,maxColor:{r:1,g:1,b:1,a:1}}}}};
 const mesh=new THREE.Mesh(new THREE.PlaneGeometry(1,1),material),root=new THREE.Group();root.add(mesh);const particle=new CafeParticle(mesh,material,new Set());
 particle.update(.7,'test');const before=mesh.position.toArray();particle.update(1.8,'test');particle.update(.7,'test');assert.deepEqual(mesh.position.toArray(),before);assert.ok(Math.abs(mesh.position.z-.7)<1e-6);
 particle.update(2.1,'test');assert.equal(mesh.visible,false);particle.update(.1,'test');assert.equal(mesh.visible,true);mesh.geometry.dispose();material.dispose();
});
test('particle gravity stays in the source world and simulation speed scales its clock',()=>{
 const c=(scalar:number)=>({minMaxState:0,scalar}),root=new THREE.Group(),emitter=new THREE.Group();emitter.rotation.z=Math.PI/2;emitter.scale.setScalar(.5);root.add(emitter);
 const material=new THREE.MeshBasicMaterial();material.userData.BA_cafeParticle={clip:'test',simulationSpeed:.5,control:{start:0,duration:10,speed:1,clipIn:0},seed:3,burst:0,delay:c(0),material:{queue:3000,shader:'test',floats:{},colors:{}},particle:{InitialModule:{startLifetime:c(3),startSpeed:c(0),gravityModifier:c(1),startSize:c(.2),startRotation:c(0),startColor:{minMaxState:0,maxColor:{r:1,g:1,b:1,a:1}}}}};
 const mesh=new THREE.Mesh(new THREE.PlaneGeometry(1,1),material);emitter.add(mesh);root.updateMatrixWorld(true);const particle=new CafeParticle(mesh,material,new Set(),root);particle.update(2,'test');root.updateMatrixWorld(true);const position=mesh.getWorldPosition(new THREE.Vector3());assert.ok(Math.abs(position.x)<1e-6);assert.ok(Math.abs(position.y+9.8100004196167/2)<1e-5);mesh.geometry.dispose();material.dispose();
});
test('source curves preserve constants and authored tangents',()=>{
 assert.equal(unityCurve({scalar:6,minMaxState:0},.5),6);
 const curve={scalar:2,minMaxState:1,maxCurve:{m_Curve:[{time:0,value:0,outSlope:0},{time:1,value:1,inSlope:0}]}};
 assert.equal(unityCurve(curve,.5),1);assert.equal(unityCurve(curve,2),2);
});

test('animated emission arc follows birth time, and orbit/radial motion survives seeking',()=>{
 const c=(scalar:number)=>({minMaxState:0,scalar});
 const shape={enabled:true,type:10,radiusThickness:0,radius:{value:1},arc:{value:360,mode:1,speed:c(1)},m_Position:{x:0,y:0,z:0},m_Rotation:{x:0,y:0,z:0},m_Scale:{x:1,y:1,z:1}};
 const quarter=particleShape(shape,1,0,1,.25);assert.ok(Math.abs(quarter.position.x)<1e-8);assert.ok(Math.abs(quarter.position.y-1)<1e-8);
 const material=new THREE.MeshBasicMaterial();material.userData.BA_cafeParticle={clip:'test',control:{start:0,duration:10,speed:1,clipIn:0},seed:1,burst:0,period:1,delay:c(0),material:{queue:3000,shader:'test',floats:{},colors:{}},particle:{ShapeModule:shape,InitialModule:{startLifetime:c(3),startSpeed:c(0),startSize:c(.2),startRotation:c(0),startColor:{minMaxState:0,maxColor:{r:1,g:1,b:1,a:1}}},VelocityModule:{enabled:true,speedModifier:c(1),orbitalZ:c(Math.PI/2),radial:c(1)}}};
 const mesh=new THREE.Mesh(new THREE.PlaneGeometry(1,1),material),root=new THREE.Group();root.add(mesh);const particle=new CafeParticle(mesh,material,new Set());
 particle.update(1,'test');assert.ok(Math.abs(mesh.position.x)<1e-6);assert.ok(Math.abs(mesh.position.y-2)<1e-6);
 const expected=mesh.position.toArray();particle.update(2.5,'test');particle.update(1,'test');assert.deepEqual(mesh.position.toArray(),expected);mesh.geometry.dispose();material.dispose();
});

test('spinning a horizontal particle keeps the ripple on the water plane',()=>{
 const c=(scalar:number)=>({minMaxState:0,scalar}),root=new THREE.Group();root.rotation.y=1.2;
 const material=new THREE.MeshBasicMaterial();material.userData.BA_cafeParticle={clip:'test',control:{start:0,duration:10,speed:1,clipIn:0},seed:2,burst:0,delay:c(0),renderer:{m_RenderMode:4,m_RenderAlignment:2},material:{queue:3000,shader:'test',floats:{},colors:{}},particle:{InitialModule:{startLifetime:c(3),startSpeed:c(0),startSize:c(1),rotation3D:true,startRotationX:c(Math.PI/2),startRotationY:c(0),startRotation:c(.7),startColor:{minMaxState:0,maxColor:{r:1,g:1,b:1,a:1}}},RotationModule:{enabled:true,separateAxes:false,curve:c(2)}}};
 const mesh=new THREE.Mesh(new THREE.PlaneGeometry(1,1),material);root.add(mesh);const particle=new CafeParticle(mesh,material,new Set());
 for(const time of [0,.2,.9,2.4]){particle.update(time,'test');root.updateMatrixWorld(true);const normal=new THREE.Vector3(0,0,1).transformDirection(mesh.matrixWorld);assert.ok(Math.abs(normal.y)>.999999);}
 mesh.geometry.dispose();material.dispose();
});

test('source active color-space flag converts particle RGB before material tint',()=>{
 const c=(scalar:number)=>({minMaxState:0,scalar}),material=new THREE.MeshBasicMaterial();material.userData.BA_cafeParticle={clip:'test',control:{start:0,duration:10,speed:1,clipIn:0},burst:0,delay:c(0),renderer:{m_ApplyActiveColorSpace:true},material:{queue:3000,shader:'test',floats:{},colors:{_Color:[2,2,2,1]}},particle:{InitialModule:{startLifetime:c(3),startSpeed:c(0),startSize:c(1),startRotation:c(0),startColor:{minMaxState:0,maxColor:{r:.5,g:.5,b:.5,a:.4}}}}};
 const mesh=new THREE.Mesh(new THREE.PlaneGeometry(1,1),material),root=new THREE.Group();root.add(mesh);const particle=new CafeParticle(mesh,material,new Set());particle.update(1,'test');
 assert.ok(Math.abs(material.color.r-.42808228)<1e-6);assert.equal(material.opacity,.4);
 material.userData.BA_cafeParticle.renderer.m_ApplyActiveColorSpace=false;particle.update(1,'test');assert.equal(material.color.r,1);mesh.geometry.dispose();material.dispose();
});
