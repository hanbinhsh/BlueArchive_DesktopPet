import {readFileSync,writeFileSync} from 'node:fs';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import assert from 'node:assert/strict';
const loader=new GLTFLoader();loader.register(()=>({name:'audit-textures',loadTexture:async()=>new THREE.Texture()}));
async function read(file:string){const bytes=readFileSync(file);return loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');}
const source=await read('.assets/furniture-exported/all/Assets/_MX/AddressableAsset/Character/CH0071/CH0071.glb'),target=await read('characters/ichika/f10206_0.glb');
const sd=source.parser.json,td=target.parser.json,name='CH0071_Cafe_my_autumnsports_01_chair_03_01';
const clip=source.animations.find(a=>a.name.startsWith(name+'--'))!,baked=target.animations.find(a=>a.name==='f10206_0')!;assert.ok(clip&&baked);
const sm=new THREE.AnimationMixer(source.scene),tm=new THREE.AnimationMixer(target.scene);
for(const [m,a]of [[sm,clip],[tm,baked]]as const){const action=m.clipAction(a);action.setLoop(THREE.LoopOnce,1);action.clampWhenFinished=true;action.play();}
const native=sd.animations.find((a:any)=>a.name===clip.name);const pairs=[];
for(const c of native.channels){const n=sd.nodes[c.target.node].name;if(!/eye|brow|blow/i.test(n))continue;const ix=td.nodes.findIndex((x:any)=>x.name===n);assert.ok(ix>=0);pairs.push({name:n,path:c.target.path,a:await source.parser.getDependency('node',c.target.node),b:await target.parser.getDependency('node',ix)});}
let max=0;
for(let i=0;i<=519;i++){
 const time=Math.min(17.3,i/30);sm.setTime(time);tm.setTime(time);
 for(const p of pairs){const key={translation:'position',rotation:'quaternion',scale:'scale'}[p.path as string]!;const a=p.a[key].toArray(),b=p.b[key].toArray();let error=Math.max(...a.map((v:number,j:number)=>Math.abs(v-b[j])));if(key==='quaternion')error=Math.min(error,Math.max(...a.map((v:number,j:number)=>Math.abs(v+b[j]))));max=Math.max(max,error);assert.ok(error<1e-4,`${time}/${p.name}/${p.path}: ${error}`);}
}
const report={complete:true,originalClip:clip.name,sampledTimes:520,eyeAndBrowChannels:pairs.length,maxComponentDifference:max,statement:'Authored eye pose is preserved, including selfie; no forced open-eye override.'};
writeFileSync('test-results/ichika042-eye-pose-proof.json',JSON.stringify(report,null,2));console.log(report);
