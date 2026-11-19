import {readFileSync,writeFileSync,readdirSync,existsSync} from 'node:fs';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {visiblePoseBounds} from '../src/framing';
const root=process.env.BA_CHARACTERS||'.assets/expanded-ready';
const loader=new GLTFLoader();loader.register(()=>({name:'audit-textures',loadTexture:async()=>new THREE.Texture()}));
const reports:any[]=process.argv.length>2&&existsSync('test-results/expanded-framing.json')?JSON.parse(readFileSync('test-results/expanded-framing.json','utf8')).filter((r:any)=>!process.argv.slice(2).includes(r.character)):[];
for(const id of readdirSync(root).filter(id=>process.argv.length<=2||process.argv.slice(2).includes(id))){
 const dir=`${root}/${id}`,c=JSON.parse(readFileSync(`${dir}/character.json`,'utf8'));
 const bytes=readFileSync(`${dir}/model.glb`),gltf=await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
 const data=gltf.parser.json.scenes[0].extras||{},v=data.BA_pet_visibility||{defaults:{},clips:{}};
 const nodes=new Map<number,THREE.Object3D>();
 for(const n of Object.keys(v.defaults))nodes.set(+n,await gltf.parser.getDependency('node',+n));
 for(const tracks of Object.values(v.clips) as any[][])for(const t of tracks)nodes.set(t.node,await gltf.parser.getDependency('node',t.node));
 const mixer=new THREE.AnimationMixer(gltf.scene),idle=THREE.AnimationClip.findByName(gltf.animations,c.animations.idle)!;
 function pose(clip:THREE.AnimationClip,t:number){
  mixer.stopAllAction();const a=mixer.clipAction(clip).reset().setLoop(THREE.LoopOnce,1);a.clampWhenFinished=true;a.play();mixer.update(t);
  for(const [n,obj] of nodes)obj.visible=v.defaults[n]??true;
  for(const tracks of [v.clips[idle.name]||[],v.clips[clip.name]||[]])for(const track of tracks){let value=track.keys[0]?.[1];for(const [time,state]of track.keys){if(time>t)break;value=state;}if(value!==undefined)nodes.get(track.node)!.visible=value;}
  gltf.scene.updateMatrixWorld(true);
 }
 pose(idle,0);const box=visiblePoseBounds(gltf.scene,c.framing?.minExtent||0),scale=2/(box.max.y-box.min.y)*c.scale,center=box.getCenter(new THREE.Vector3());
 const rows:any[]=[];const rejected=new Set<string>();
 for(const a of c.actions){
  const clip=THREE.AnimationClip.findByName(gltf.animations,a.clip)!;
  if(!clip){throw Error(`${id}/${a.id}: missing clip`);}
  let minY=0,maxY=2,radius=0;const hiddenSamples:number[]=[];
  for(const fraction of Array.from({length:121},(_,i)=>i/120)){
   pose(clip,clip.duration*fraction);const b=visiblePoseBounds(gltf.scene,.003);
   if(b.isEmpty()&&a.id.startsWith('original_')){
    gltf.scene.traverse(o=>{if(!o.matrixWorld.elements.every(Number.isFinite))throw Error(`${id}/${a.id}: invalid matrix`);});
    hiddenSamples.push(fraction);continue;
   }
   const values=[(b.min.y-box.min.y)*scale,(b.max.y-box.min.y)*scale,(b.min.x-center.x)*scale,(b.max.x-center.x)*scale];
   if(!values.every(Number.isFinite))throw Error(`${id}/${a.id}: nonfinite pose at ${fraction}; empty=${b.isEmpty()}`);
   minY=Math.min(minY,values[0]);maxY=Math.max(maxY,values[1]);radius=Math.max(radius,Math.abs(values[2]),Math.abs(values[3]));
  }
  const need=minY<-.4||maxY>2.4||radius>1.44;
  if(hiddenSamples.length===121){rejected.add(a.id);rows.push({id:a.id,sourceName:a.sourceName,status:'requires-scene',reason:'Character collapsed or hidden at all sampled times',hiddenSamples});continue;}
  const centerY=(minY+maxY)/2,zoom=Math.min(1,2.75/(maxY-minY),1.4/Math.max(radius,.01));
  // Keep reviewed common actions unchanged, including existing authored cameras.
  if(a.id.startsWith('original_')&&need){
   if(zoom<.25||Math.abs(centerY)>5){rejected.add(a.id);rows.push({id:a.id,sourceName:a.sourceName,status:'requires-scene',minY,maxY,radius});continue;}
   c.framing??={};c.framing.actions??={};c.framing.actions[a.id]={zoom,centerY};
  }
  rows.push({id:a.id,status:'finite',duration:clip.duration,minY,maxY,radius,camera:c.framing?.actions?.[a.id],...(hiddenSamples.length?{hiddenSamples}:{})});
 }
 c.actions=c.actions.filter((a:any)=>!rejected.has(a.id));
 writeFileSync(`${dir}/character.json`,JSON.stringify(c,null,2));reports.push({character:id,actions:rows});
 writeFileSync('test-results/expanded-framing.json',JSON.stringify(reports,null,2));console.log(id,rows.length,'sampled;',rejected.size,'scene-dependent');
 mixer.stopAllAction();mixer.uncacheRoot(gltf.scene);
 gltf.scene.traverse((o:any)=>{if(o.isMesh){o.geometry.dispose();for(const m of Array.isArray(o.material)?o.material:[o.material])m.dispose();}});
}
