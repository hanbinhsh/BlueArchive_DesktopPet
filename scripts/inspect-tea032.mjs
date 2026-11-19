import {readFileSync} from 'node:fs';import * as T from 'three';import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
globalThis.ProgressEvent=class{};
const bytes=readFileSync('characters/mine/f207310_0.glb');const len=bytes.readUInt32LE(12);let d=JSON.parse(bytes.subarray(20,20+len));d.images=[];d.textures=[];for(const m of d.materials){delete m.pbrMetallicRoughness.baseColorTexture;}
const raw=bytes.subarray(28+len);d.buffers=[{uri:'data:application/octet-stream;base64,'+raw.toString('base64'),byteLength:raw.length}];
const g=await new GLTFLoader().parseAsync(JSON.stringify(d),'');const mixer=new T.AnimationMixer(g.scene);mixer.clipAction(g.animations[0]).play();
for(const t of [0,16.2333,16.8,17,17.4,18]){mixer.setTime(t);g.scene.updateMatrixWorld(true);console.log(t);g.scene.traverse(n=>{if(/bone_table_0[12]$/.test(n.name))console.log(n.name,n.getWorldPosition(new T.Vector3()).toArray(),n.getWorldScale(new T.Vector3()).toArray());});}
