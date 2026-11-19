import {readFileSync,writeFileSync} from 'node:fs';import assert from 'node:assert/strict';import * as T from 'three';import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {CafeParticle} from '../src/cafe-particles.ts';import {ParticleTransforms} from '../src/particle-transforms.ts';
globalThis.ProgressEvent=class{};
const bytes=readFileSync('characters/hanako_swimsuit/f210316_0.glb'),len=bytes.readUInt32LE(12),d=JSON.parse(bytes.subarray(20,20+len));d.images=[];d.textures=[];for(const m of d.materials)delete m.pbrMetallicRoughness.baseColorTexture;
const raw=bytes.subarray(28+len);d.buffers=[{uri:'data:application/octet-stream;base64,'+raw.toString('base64'),byteLength:raw.length}];
const g=await new GLTFLoader().parseAsync(JSON.stringify(d),''),targets=[],seen=new Set();
g.scene.traverse(n=>{const s=n.material?.userData.BA_cafeParticle;if(s&&s.simulationSpace===1&&(s.burst>=1||s.control.start>=1)&&!seen.has(s.sourceName)){seen.add(s.sourceName);targets.push(n);}});
const mixer=new T.AnimationMixer(g.scene);mixer.clipAction(g.animations[0]).play();const report=[];
for(const mesh of targets){
 // Keep the same integration rate; an epsilon force isolates gravity without changing velocity quadrature.
 const noGravity=new T.Mesh(mesh.geometry,mesh.material.clone());noGravity.material.userData=structuredClone(mesh.material.userData);noGravity.material.userData.BA_cafeParticle.particle.InitialModule.gravityModifier={minMaxState:0,scalar:1e-30};mesh.parent.add(noGravity);
 const frames=new ParticleTransforms(g.scene,g.animations),p=new CafeParticle(mesh,mesh.material,new Set(),g.scene,frames),zero=new CafeParticle(noGravity,noGravity.material,new Set(),g.scene,frames),birth=p.emissionState(0).time;
 const row={source:mesh.material.userData.BA_cafeParticle.sourceName,birth,samples:[]};
 // Authored orbital velocity also deflects the trajectory laterally; require downward gravity displacement, not zero X/Z.
 for(const age of [.1,.2,.3]){const time=birth+age;mixer.setTime(time);g.scene.updateMatrixWorld(true);p.update(time,g.animations[0].name);zero.update(time,g.animations[0].name);g.scene.updateMatrixWorld(true);const delta=mesh.getWorldPosition(new T.Vector3()).sub(noGravity.getWorldPosition(new T.Vector3()));assert.ok(mesh.visible);assert.ok(delta.y<-.001,JSON.stringify(delta));row.samples.push({time,gravityDisplacement:delta.toArray()});}
 report.push(row);mesh.parent.remove(noGravity);
}
assert.equal(report.length,2);writeFileSync('test-results/lemon032-gravity-numeric.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
