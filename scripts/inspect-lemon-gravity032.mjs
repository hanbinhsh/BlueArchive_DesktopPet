import {readFileSync} from 'node:fs';import * as T from 'three';import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
globalThis.ProgressEvent=class{};
const bytes=readFileSync('characters/hanako_swimsuit/f210316_0.glb'),len=bytes.readUInt32LE(12),d=JSON.parse(bytes.subarray(20,20+len));
d.images=[];d.textures=[];for(const m of d.materials)delete m.pbrMetallicRoughness.baseColorTexture;
const raw=bytes.subarray(28+len);d.buffers=[{uri:'data:application/octet-stream;base64,'+raw.toString('base64'),byteLength:raw.length}];
const g=await new GLTFLoader().parseAsync(JSON.stringify(d),'');g.scene.updateMatrixWorld(true);
const rows=[];const seen=new Set();g.scene.traverse(n=>{let s=n.material?.userData.BA_cafeParticle;if(s&&s.particle.InitialModule.gravityModifier.scalar&&!seen.has(s.sourceName)){seen.add(s.sourceName);let matrix=n.parent.matrixWorld.clone();rows.push({n,s,matrix});}});
const mixer=new T.AnimationMixer(g.scene);mixer.clipAction(g.animations[0]).play();
for(const t of [0,1,3,5,7,10,14]){mixer.setTime(t);g.scene.updateMatrixWorld(true);console.log('TIME',t);for(const {n,s,matrix}of rows){const local=new T.Vector3(0,-1,0).applyMatrix3(new T.Matrix3().setFromMatrix4(matrix.clone().invert()));const now=local.applyMatrix3(new T.Matrix3().setFromMatrix4(n.parent.matrixWorld));console.log(s.sourceName.split('/').at(-1),'gravity',now.toArray().map(n=>+n.toFixed(3)),'pos',n.parent.getWorldPosition(new T.Vector3()).toArray());}}
