import {readFileSync} from 'node:fs';
import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const loader=new GLTFLoader();loader.register(()=>({name:'no-textures',loadTexture:async()=>new T.Texture()}));
for(const name of process.argv.slice(2)){
 const c=JSON.parse(readFileSync(`characters/${name}/character.json`));
 for(const f of c.furniture){
  const bytes=readFileSync(`characters/${name}/${f.model}`);const json=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)));
  const gltf=await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
  const mix=new T.AnimationMixer(gltf.scene),clip=gltf.animations[0];mix.clipAction(clip).play();
  const v=json.scenes[0].extras.BA_pet_visibility,objects=new Map();
  for(const i of new Set([...Object.keys(v.defaults).map(Number),...v.clips[f.clip].map(t=>t.node)]))objects.set(i,await gltf.parser.getDependency('node',i));
  for(const time of [0,.1,clip.duration/2,clip.duration*.99]){
   mix.setTime(time);for(const [i,b] of Object.entries(v.defaults))objects.get(+i).visible=b;
   for(const tr of v.clips[f.clip]){let b=tr.keys[0]?.[1];for(const [t,s]of tr.keys){if(t>time)break;b=s;}objects.get(tr.node).visible=b;}
   gltf.scene.updateMatrixWorld(true);const meshes=[];
   gltf.scene.traverseVisible(o=>{if(o.isMesh){if(o.isSkinnedMesh)o.computeBoundingBox();const box=new T.Box3().setFromObject(o);meshes.push({name:o.name,size:box.getSize(new T.Vector3()).toArray(),center:box.getCenter(new T.Vector3()).toArray()});}});
   console.log(name,f.id,time,JSON.stringify(meshes.sort((a,b)=>Math.max(...b.size,...b.center.map(Math.abs))-Math.max(...a.size,...a.center.map(Math.abs))).slice(0,8)));
  }
 }
}
