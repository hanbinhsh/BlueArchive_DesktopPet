import {readFileSync,writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {visiblePoseBounds} from '../src/framing';
import {HaloFollower} from '../src/halo';
const specs=JSON.parse(readFileSync(process.env.BA_ROSTER_SPECS||'scripts/roster-extras.json','utf8'));
const loader=new GLTFLoader();
loader.register(()=>({name:'audit-textures',loadTexture:async()=>new THREE.Texture()}));
const report=[];
for(const id of Object.keys(specs)){
 const dir=`characters/${id}`, manifest=JSON.parse(readFileSync(`${dir}/character.json`,'utf8'));
 const bytes=readFileSync(`${dir}/model.glb`), gltf=await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
 const data=gltf.parser.json.scenes[0].extras, visibility=data.BA_pet_visibility;
 const nodes=new Map<number,THREE.Object3D>();
 for(const key of Object.keys(visibility.defaults))nodes.set(+key,await gltf.parser.getDependency('node',+key));
 for(const tracks of Object.values(visibility.clips) as any[][])for(const t of tracks)nodes.set(t.node,await gltf.parser.getDependency('node',t.node));
 const idleClip=THREE.AnimationClip.findByName(gltf.animations,manifest.animations.idle)!;
 const mixer=new THREE.AnimationMixer(gltf.scene);
 function pose(clip:THREE.AnimationClip,time:number){
  mixer.stopAllAction();
  const action=mixer.clipAction(clip).reset().setLoop(THREE.LoopOnce,1);action.clampWhenFinished=true;action.play();mixer.update(time);
  for(const [n,obj] of nodes)obj.visible=visibility.defaults[n]??true;
  for(const tracks of [visibility.clips[idleClip.name]||[],visibility.clips[clip.name]||[]])for(const track of tracks){
   let value=track.keys[0]?.[1];for(const [t,v]of track.keys){if(t>time)break;value=v;}
   if(value!==undefined)nodes.get(track.node)!.visible=value;
  }
  gltf.scene.updateMatrixWorld(true);
 }
 pose(idleClip,0);
 const box=visiblePoseBounds(gltf.scene,manifest.framing?.minExtent||0), scale=2/(box.max.y-box.min.y)*manifest.scale, center=box.getCenter(new THREE.Vector3());
 const samples=[];
 for(const action of manifest.actions){
  const clip=THREE.AnimationClip.findByName(gltf.animations,action.clip)!;
  const sampleCount=Number(process.env.BA_FRAMING_SAMPLES||0);
  for(const fraction of sampleCount?Array.from({length:sampleCount},(_,i)=>i/(sampleCount-1)):[0,.1,.25,.5,.75,.95]){
   pose(clip,clip.duration*fraction);
   if(data.BA_halo_follow){
    const spec=data.BA_halo_follow,follow=new HaloFollower(await gltf.parser.getDependency('node',spec.node),await gltf.parser.getDependency('node',spec.target),spec);
    for(let i=0;i<30;i++)follow.update(1/30);
   }
   // Ignore subpixel props parked offstage by the original scale tracks.
   // At the default display size .003 world units is well below one pixel.
   const bounds=visiblePoseBounds(gltf.scene,.003);
   const frame={minX:(bounds.min.x-center.x)*scale,maxX:(bounds.max.x-center.x)*scale,minY:(bounds.min.y-box.min.y)*scale,maxY:(bounds.max.y-box.min.y)*scale};
   const view=manifest.framing?.actions?.[action.id];
   if(view){frame.minX*=view.zoom;frame.maxX*=view.zoom;frame.minY=(frame.minY-view.centerY)*view.zoom+1;frame.maxY=(frame.maxY-view.centerY)*view.zoom+1;}
   assert.ok(Object.values(frame).every(Number.isFinite),`${id}/${action.id}: finite pose`);
   const fits=frame.minX>-1.51&&frame.maxX<1.51&&frame.minY>-.46&&frame.maxY<2.46;
   if(!process.env.BA_FRAMING_SCAN)assert.ok(fits,`${id}/${action.id}@${fraction}: outside pet frame ${JSON.stringify(frame)}`);
   else if(!fits)console.log('OUTSIDE',id,action.id,fraction,JSON.stringify(frame));
   if(!fits&&process.env.BA_FRAMING_DETAILS)gltf.scene.traverseVisible((o:any)=>{if(o.isMesh){const b=visiblePoseBounds(o);console.log(o.name,b.min.toArray(),b.getSize(new THREE.Vector3()).toArray());}});
   samples.push({action:action.id,fraction,...frame});
  }
 }
 report.push({character:id,samples});console.log(id,process.env.BA_FRAMING_SCAN?'sampled':'all action sample bounds fit');
}
writeFileSync(process.env.BA_FRAMING_REPORT||'test-results/extra-framing.json',JSON.stringify(report,null,2));
