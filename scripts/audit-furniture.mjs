import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { visiblePoseBounds } from '../src/framing.ts';
const loader=new GLTFLoader();loader.register(()=>({name:'audit-textures',loadTexture:async()=>new THREE.Texture()}));
const root=process.env.BA_CHARACTERS||'characters';
const report=[];
for(const dir of readdirSync(root,{withFileTypes:true}).filter(d=>d.isDirectory())){
 if(process.argv.length>2&&!process.argv.slice(2).includes(dir.name))continue;
 const c=JSON.parse(readFileSync(`${root}/${dir.name}/character.json`,'utf8'));
 for(const f of c.furniture||[]){
  const bytes=readFileSync(`${root}/${dir.name}/${f.model}`),size=bytes.readUInt32LE(12),json=JSON.parse(bytes.subarray(20,20+size));
  assert.equal(bytes.readUInt32LE(8),bytes.length);assert.ok(![...(json.images||[]),...(json.buffers||[])].some(x=>x.uri));
  const gltf=await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
  gltf.scene.traverse(o=>{if(o.isMesh)o.userData.BA_auxiliary=(Array.isArray(o.material)?o.material:[o.material]).every(m=>m.userData.BA_stencil);});
  const clip=THREE.AnimationClip.findByName(gltf.animations,f.clip);assert.ok(clip);assert.ok(Math.abs(clip.duration-f.duration)<.001);
  const extras=json.scenes[0].extras,v=extras.BA_pet_visibility;
  const objects=new Map();for(const n of new Set([...Object.keys(v.defaults).map(Number),...v.clips[f.clip].map(t=>t.node)]))objects.set(n,await gltf.parser.getDependency('node',n));
  const mixer=new THREE.AnimationMixer(gltf.scene),action=mixer.clipAction(clip).setLoop(THREE.LoopOnce,1);action.clampWhenFinished=true;action.play();
  const sizes=[];let meshes=0,bones=0;gltf.scene.traverse(o=>{if(o.isMesh)meshes++;if(o.isBone)bones++;});
  for(let i=0;i<=120;i++){
   const time=clip.duration*i/120;mixer.setTime(time);
   for(const [n,value]of Object.entries(v.defaults))objects.get(Number(n)).visible=value;
   for(const tr of v.clips[f.clip]){let value=tr.keys[0]?.[1];for(const [t,state]of tr.keys){if(t>time+1e-6)break;value=state;}if(value!==undefined)objects.get(tr.node).visible=value;}
   gltf.scene.updateMatrixWorld(true);
   gltf.scene.traverse(o=>assert.ok(o.matrixWorld.elements.every(Number.isFinite),`${dir.name}/${f.id} nonfinite transform`));
   const box=visiblePoseBounds(gltf.scene,.003);
   const s=box.getSize(new THREE.Vector3()).toArray();assert.ok(s.every(Number.isFinite));sizes.push(s);
  }
  const dimensions=[0,1,2].map(i=>Math.max(...sizes.map(s=>s[i])));
  if(dir.name==='junko_newyear')assert.ok(Math.max(...dimensions)<5,'Collapsed partner weapon must not expand framing');
  if(dir.name==='mutsuki_dress')assert.ok(Math.max(...dimensions)<3,'Rigid prop must not stretch across the room');
  const ratio=[0,1,2].map(i=>{const sorted=sizes.map(s=>s[i]).sort((a,b)=>a-b);return dimensions[i]/Math.max(sorted[Math.floor(sorted.length*.9)],1e-6);});
  assert.ok(ratio.every(v=>v<5),`${dir.name}/${f.id}: geometry spike ${ratio}`);
  for(const m of [c.mouth,...(extras.BA_furniture_mouths||[])].filter(Boolean))assert.ok(json.materials.some(mat=>mat.name===m.material));
  report.push({character:dir.name,id:f.id,duration:f.duration,meshes,bones,dimensions,maxTo90thPercentile:ratio,partners:(extras.BA_furniture_mouths||[]).length});
  mixer.stopAllAction();gltf.scene.traverse(o=>{if(o.isMesh){o.geometry.dispose();for(const m of Array.isArray(o.material)?o.material:[o.material])m.dispose();}});
  console.log('AUDIT',dir.name,f.id);
 }
}
writeFileSync(`test-results/${process.env.BA_FURNITURE_AUDIT||'furniture-assets'}.json`,JSON.stringify(report,null,2));
