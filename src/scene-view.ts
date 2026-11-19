import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { mouthTransform,type Character,type Furniture,type Settings } from './shared';
import { effectiveSpeed } from './activities';
import { EyeFollower } from './eyes';
import { HaloFollower } from './halo';
import { PropTransitions } from './prop-transitions';
import { attachWaterFx } from './furniture-fx';
import { attachCafeSmoke,type CafeDepth } from './cafe-smoke';
import { ModelOutline } from './model-outline';
import { CafeParticle } from './cafe-particles';
import { ParticleTransforms } from './particle-transforms';
import { CafeTrail } from './cafe-trails';
import { attachLiquidReceiver } from './liquid-receiver';
import { visiblePoseBounds } from './framing';
import { updateFxBillboard } from './fx-billboard';
import { attachPoolWater } from './pool-water';
import { PlanarMirror } from './mirror-surface';
type Tracks = {node:number;keys:[number,boolean][]}[];
export class SceneView {
 readonly scene=new THREE.Scene();readonly camera=new THREE.OrthographicCamera(-1,1,1,-1,.01,100);readonly root=new THREE.Group();
 readonly actions=new Map<string,THREE.AnimationAction>();
 mixer!:THREE.AnimationMixer;active!:THREE.AnimationAction;idle!:THREE.AnimationAction;eye!:EyeFollower;props!:PropTransitions;
 character!:Character;furniture?:Furniture;finished=false;actionId='idle';mouthTile:number|null=null;mouthFlipped=false;
 private mouths:{spec:NonNullable<Character['mouth']>;map:THREE.Texture}[]=[];
 private halos:HaloFollower[]=[];private vis=new Map<number,THREE.Object3D>();private defaults:Record<string,boolean>={};private tracks:Record<string,Tracks>={};private idleTracks:Tracks=[];
 private fxUpdates:((time:number)=>void)[]=[];private mouthLooped=false;private ambientLoopOffset=0;
 private particles:CafeParticle[]=[];private outline?:ModelOutline;
 private trails:CafeTrail[]=[];
 private mirrors:PlanarMirror[]=[];
 private billboards:THREE.Object3D[]=[];
 private depth:CafeDepth={texture:{value:null},size:{value:new THREE.Vector2()},range:{value:new THREE.Vector2(.01,100)},scale:{value:1},required:false};
 private depthTarget?:THREE.WebGLRenderTarget;
 private fading?:THREE.AnimationAction;private fadeLeft=0;private blinkElapsed=0;private turnTarget:number|null=null;
 private cameraBlend?:{zoom:number;y:number;fromZoom:number;fromY:number;elapsed:number;duration:number};
 private geometries=new Set<THREE.BufferGeometry>();private materials=new Set<THREE.Material>();private textures=new Set<THREE.Texture>();private skeletons=new Set<THREE.Skeleton>();
 readonly durations:Record<string,number>={};meshes=0;bones=0;disposed=false;
 static async create(payload:{character:Character;furniture?:Furniture;model:ArrayBuffer},settings:Settings):Promise<SceneView>{
  const v=new SceneView();try{await v.load(payload,settings);return v;}catch(e){v.dispose();throw e;}
 }
 private async load({character,furniture,model}:{character:Character;furniture?:Furniture;model:ArrayBuffer},settings:Settings){
  this.character=character;this.furniture=furniture;
  const bytes=new Uint8Array(model),length=new DataView(model).getUint32(12,true),json=JSON.parse(new TextDecoder().decode(bytes.slice(20,20+length)));
  if([...(json.images||[]),...(json.buffers||[])].some(i=>i.uri))throw Error('角色资源必须内嵌贴图');
  const gltf=await new GLTFLoader().parseAsync(model,'');this.root.add(gltf.scene);this.scene.add(this.root);
  this.scene.matrixWorldAutoUpdate=false;this.camera.position.set(0,1,8);this.camera.lookAt(0,1,0);
  const particleTransforms=new ParticleTransforms(gltf.scene,gltf.animations);
  gltf.scene.traverse(o=>{
   if(o.userData.BA_fxBillboard)this.billboards.push(o);
   if((o as THREE.Bone).isBone)this.bones++;
   const mesh=o as THREE.Mesh;if(!mesh.isMesh)return;this.meshes++;mesh.frustumCulled=false;this.geometries.add(mesh.geometry);
   if((o as THREE.SkinnedMesh).isSkinnedMesh)this.skeletons.add((o as THREE.SkinnedMesh).skeleton);
   const mats=Array.isArray(mesh.material)?mesh.material:[mesh.material];
   for(const m of mats){this.materials.add(m);for(const value of Object.values(m))if(value instanceof THREE.Texture)this.textures.add(value);
    if(m.userData.BA_depthWrite===false)m.depthWrite=false;
    if(Number.isFinite(m.userData.BA_renderOrder))mesh.renderOrder=m.userData.BA_renderOrder;
    if(m.userData.BA_smokeFx?.kind==='channel')mesh.geometry.setAttribute('fxSecondUV',mesh.geometry.getAttribute('uv1')||new THREE.BufferAttribute(new Float32Array(mesh.geometry.getAttribute('position').count*2),2));
    if(m.userData.BA_cafeParticle)this.particles.push(new CafeParticle(mesh,m as THREE.MeshBasicMaterial,this.textures,gltf.scene,particleTransforms));
    if(m.userData.BA_cafeTrail)this.trails.push(new CafeTrail(mesh,m as THREE.MeshBasicMaterial,mesh.parent!,gltf.scene,particleTransforms));
    if(furniture&&m.userData.BA_mirrorSurface){this.mirrors.push(new PlanarMirror(mesh,typeof m.userData.BA_mirrorSurface==='object'?m.userData.BA_mirrorSurface:{}));break;}
    if(furniture&&m.userData.BA_clipStencil){m.stencilWrite=true;m.stencilRef=m.userData.BA_clipStencil;m.stencilFunc=THREE.EqualStencilFunc;m.stencilZPass=THREE.KeepStencilOp;}
    const s=m.userData.BA_stencil;if(!furniture||!s)continue;
    m.stencilWrite=true;m.stencilRef=s.ref;m.stencilFunc=s.mode==='mask'?THREE.GreaterEqualStencilFunc:s.mode==='equal'?THREE.EqualStencilFunc:THREE.NotEqualStencilFunc;m.stencilZPass=s.mode==='mask'?THREE.ReplaceStencilOp:THREE.KeepStencilOp;
    if(s.mode==='mask'){m.colorWrite=false;m.depthWrite=false;m.depthTest=false;m.transparent=false;}mesh.renderOrder=s.order;
   }
   mesh.userData.BA_auxiliary=!!furniture&&mats.every(m=>!!m.userData.BA_stencil||!!m.userData.BA_maskedFx);
  });
  const particleByName=new Map(this.particles.map(p=>[p.name,p]));
  gltf.scene.traverse(o=>{
   const spawn=o.userData.BA_subEmitter;if(!spawn)return;
   const parent=particleByName.get(spawn.parent);if(!parent)throw Error('缺少子发射器父粒子：'+spawn.parent);
   const event=parent.emissionState(spawn.event);o.position.copy(event.position);particleTransforms.refresh(o);
   o.traverse(child=>{const particle=particleByName.get(child.name);if(particle){particle.startAt(event.time);particle.inheritFrom(event,spawn.properties||0);}});
  });
  for(const material of this.materials){for(const update of [await attachPoolWater(material as THREE.MeshBasicMaterial,gltf.parser,this.textures),await attachWaterFx(material as THREE.MeshBasicMaterial,gltf.parser,this.textures),await attachCafeSmoke(material as THREE.MeshBasicMaterial,gltf.parser,this.textures,this.depth)])if(update)this.fxUpdates.push(update);}
  for(const material of this.materials){const update=attachLiquidReceiver(material,gltf.scene);if(update)this.fxUpdates.push(update);}
  const extras=json.scenes?.[0]?.extras||{},visibility=extras.BA_pet_visibility;
  if(visibility){this.defaults=visibility.defaults;this.tracks=visibility.clips;const indices=new Set<number>(Object.keys(this.defaults).map(Number));for(const t of Object.values(this.tracks))for(const tr of t)indices.add(tr.node);for(const i of indices)this.vis.set(i,await gltf.parser.getDependency('node',i));}
  for(const h of [extras.BA_halo_follow,...(extras.BA_halo_follow_extra||[])].filter(Boolean))this.halos.push(new HaloFollower(await gltf.parser.getDependency('node',h.node),await gltf.parser.getDependency('node',h.target),h));
  const specs:NonNullable<Character['mouth']>[]=[...(extras.BA_furniture_mouths||[])];
  if(character.mouth){const spec=structuredClone(character.mouth);if(furniture)spec.events=Object.fromEntries((character.furniture||[]).filter(f=>f.model===furniture.model).map(f=>[f.clip,f.mouthEvents]));specs.push(spec);}
  for(const spec of specs){
   const m=[...this.materials].find(m=>m.name===spec.material) as THREE.MeshBasicMaterial|undefined;if(!m?.map)throw Error('缺少口型贴图：'+spec.material);
   // GLTFLoader shares textures with identical embedded images/samplers, even
   // across different texture indices. Each mouth needs independent UV state.
   const map=m.map.clone();m.map=map;this.textures.add(map);this.mouths.push({spec,map});
  }
  this.mixer=new THREE.AnimationMixer(gltf.scene);
  const entries=furniture?(character.furniture||[]).filter(f=>f.model===furniture.model).map(f=>({id:f.id,clip:f.clip})):(character.actions||[]);
  for(const e of entries){const clip=THREE.AnimationClip.findByName(gltf.animations,e.clip);if(!clip)throw Error('缺少动画：'+e.id);this.actions.set(e.id,this.mixer.clipAction(clip));this.durations[`${furniture?'furniture':'action'}:${e.id}`]=clip.duration;}
  const initialName=furniture?.clip||character.animations.idle,initial=THREE.AnimationClip.findByName(gltf.animations,initialName);if(!initial)throw Error('缺少待机动画');
  this.idle=this.mixer.clipAction(initial);this.active=this.idle;this.active.play();this.idleTracks=this.tracks[initialName]||[];this.mixer.update(0);this.visibility();gltf.scene.updateMatrixWorld(true);
  const box=visiblePoseBounds(gltf.scene,furniture?.003:(character.framing?.minExtent||0));
  if(furniture){for(const a of this.actions.values()){this.mixer.stopAllAction();this.active=a.reset().play();for(let i=0;i<=120;i++){this.mixer.setTime(a.getClip().duration*i/120);this.visibility();gltf.scene.updateMatrixWorld(true);box.union(visiblePoseBounds(gltf.scene,.003));}}}
  this.mixer.stopAllAction();this.active=this.idle.reset().play();this.mixer.update(0);this.visibility();
  const height=box.max.y-box.min.y;if(!Number.isFinite(height)||height<=0)throw Error('模型没有可显示的几何体');
  const scale=(furniture?Math.min(2/height,2.45/Math.hypot(box.max.x-box.min.x,box.max.z-box.min.z)):2/height)*character.scale,center=box.getCenter(new THREE.Vector3());
  gltf.scene.scale.multiplyScalar(scale);gltf.scene.position.set(-center.x*scale,furniture?-center.y*scale:-box.min.y*scale-1,-center.z*scale);this.root.position.y=1;
  this.depth.scale.value=scale;
  if(furniture){this.camera.position.set(0,4.2,8);this.camera.lookAt(0,1,0);}
  this.scene.add(new THREE.HemisphereLight(0xffffff,0xcbd5e1,2.3));const light=new THREE.DirectionalLight(0xffffff,2);light.position.set(-3,6,6);this.scene.add(light);
  this.eye=new EyeFollower(gltf.scene);this.props=new PropTransitions(gltf.scene);this.outline=new ModelOutline(gltf.scene);
  this.mixer.addEventListener('finished',e=>{if(e.action===this.active)this.finished=true;});
  this.mixer.addEventListener('loop',e=>{if(e.action===this.active){this.mouthLooped=true;this.ambientLoopOffset+=e.loopDelta*e.action.getClip().duration;}});
  this.orientation(settings,0,false);this.play(furniture?.id||'idle',settings,true);this.resize(settings.size);this.scene.updateMatrixWorld(true);
 }
 resize(size:number){const width=Math.round(size*1.5),height=Math.round(size*1.45);this.camera.left=-width/size;this.camera.right=width/size;this.camera.top=height/size;this.camera.bottom=-height/size;this.camera.updateProjectionMatrix();}
 render(renderer:THREE.WebGLRenderer){
  if(this.depth.required){
   const size=renderer.getDrawingBufferSize(this.depth.size.value),oldTarget=renderer.getRenderTarget();
   if(!this.depthTarget){this.depthTarget=new THREE.WebGLRenderTarget(size.x,size.y,{stencilBuffer:true});this.depthTarget.depthTexture=new THREE.DepthTexture(size.x,size.y,THREE.UnsignedInt248Type);this.depthTarget.depthTexture.format=THREE.DepthStencilFormat;}
   this.depthTarget.setSize(size.x,size.y);this.depth.range.value.set(this.camera.near,this.camera.far);
   // Preserve alpha tests and invisible depth masks without letting smoke
   // contribute to its own intersection depth or sample the active target.
   const hidden:THREE.Object3D[]=[];
   this.scene.traverse(o=>{const m=o as THREE.Mesh;if(!m.isMesh||!m.visible)return;const mats=Array.isArray(m.material)?m.material:[m.material];if(mats.every(mat=>mat.transparent&&!mat.depthWrite)){m.visible=false;hidden.push(m);}});
   try{renderer.setRenderTarget(this.depthTarget);renderer.clear();renderer.render(this.scene,this.camera);}
   finally{for(const o of hidden)o.visible=true;renderer.setRenderTarget(oldTarget);}
   this.depth.texture.value=this.depthTarget.depthTexture;
  }
  for(const mirror of this.mirrors)mirror.render(renderer,this.scene,this.camera);
  renderer.render(this.scene,this.camera);
 }
 orientation(s:Settings,roaming:number,smooth:boolean){const yaw=(roaming?roaming*Math.PI/2:s.yaw)+this.character.yaw+(this.furniture?(this.furniture.yaw??Math.PI*.75):0);if(smooth)this.turnTarget=yaw;else{this.root.rotation.set(roaming?0:s.pitch,yaw,roaming?0:s.roll,'YXZ');this.turnTarget=null;}}
 play(id:string,s:Settings,loop=false,count=1){
  const next=this.actions.get(id)||(id==='idle'?this.idle:undefined);if(!next)return;
  if(this.furniture&&this.furniture.id!==id){
   const selected=this.character.furniture?.find(f=>f.id===id&&f.model===this.furniture!.model);
   if(selected){this.furniture=selected;this.orientation(s,0,false);}
  }
  this.finished=false;this.blinkElapsed=0;this.mouthLooped=false;this.ambientLoopOffset=0;this.actionId=id;
  const duration=.18/effectiveSpeed(s).transition;
  if(!this.furniture){const v=this.character.framing?.actions?.[id]||{zoom:1,centerY:1};this.cameraBlend={zoom:v.zoom,y:v.centerY,fromZoom:this.camera.zoom,fromY:this.camera.position.y,elapsed:0,duration};}
  if(this.fading){this.fading.stop();this.fading=undefined;}
  const previous=this.active;next.reset().setEffectiveWeight(1).setEffectiveTimeScale(effectiveSpeed(s).playback);next.setLoop(loop||count>1?THREE.LoopRepeat:THREE.LoopOnce,loop?Infinity:count);next.clampWhenFinished=true;next.play();
  if(previous&&previous!==next){this.props.begin(next.getClip(),duration);previous.stopFading().setEffectiveWeight(1).crossFadeTo(next,duration,false);this.fading=previous;this.fadeLeft=duration;}
  this.active=next;this.mouth();
 }
 hold(){this.active.paused=true;}
 update(dt:number,s:Settings,cursor:{x:number;y:number},roaming:number,allowBlink:boolean){
  this.outline?.apply(s.outline,s.outlineWidth);
  const rate=roaming? s.roamSpeed/35:effectiveSpeed(s).playback;
  // Action clocks scale; mixer time and cross-fade clocks remain real time.
  if(!this.active.paused)this.active.setEffectiveTimeScale(rate);if(this.fading)this.fading.setEffectiveTimeScale(rate);
  if(this.cameraBlend){const b=this.cameraBlend;b.elapsed=Math.min(b.duration,b.elapsed+dt);const t=b.elapsed/b.duration,w=t*t*(3-2*t);this.camera.zoom=THREE.MathUtils.lerp(b.fromZoom,b.zoom,w);const y=THREE.MathUtils.lerp(b.fromY,b.y,w);this.camera.position.y=y;this.camera.lookAt(0,y,0);this.camera.updateProjectionMatrix();if(t===1)this.cameraBlend=undefined;}
  if(this.turnTarget!==null){const targets={x:roaming?0:s.pitch,y:this.turnTarget,z:roaming?0:s.roll};let complete=true;for(const axis of ['x','y','z'] as const){const delta=Math.atan2(Math.sin(targets[axis]-this.root.rotation[axis]),Math.cos(targets[axis]-this.root.rotation[axis]));if(Math.abs(delta)>.001)complete=false;this.root.rotation[axis]+=Math.sign(delta)*Math.min(Math.abs(delta),dt*Math.PI*2);}if(complete){this.root.rotation.set(targets.x,targets.y,targets.z,'YXZ');this.turnTarget=null;}}
  if(allowBlink&&!this.furniture&&this.character.idleBlink&&this.active===this.idle){this.blinkElapsed+=dt;if(this.blinkElapsed>=this.character.idleBlink.interval)this.play(this.character.idleBlink.action,s);}
  this.eye.reset();this.mixer.update(dt);if(this.fading){this.fadeLeft-=dt;if(this.fadeLeft<=0){this.fading.stop();this.fading=undefined;}}
  this.mouth();this.visibility();for(const o of this.billboards)updateFxBillboard(o,this.camera,o.userData.BA_fxBillboard.fixedY);for(const particle of this.particles)particle.update(this.active.time,this.active.getClip().name,this.camera,undefined,this.active.time+this.ambientLoopOffset);
  for(const trail of this.trails)trail.update(this.active.time,this.active.getClip().name,this.camera);
  // Shader UV scrolling uses a continuous clock in the source engine. Resetting
  // it at each animation loop teleports the pool's colour/foam pattern.
  for(const update of this.fxUpdates)update(this.active.time+this.ambientLoopOffset);this.scene.updateMatrixWorld(true);for(const h of this.halos)h.update(dt);
  this.eye.update(!this.furniture&&s.eyeFollow&&!roaming&&allowBlink&&this.active===this.idle&&Math.cos(this.root.rotation.y)>.3&&Math.cos(s.pitch)>Math.cos(.7)&&Math.cos(s.roll)>Math.cos(.7),cursor,innerWidth,innerHeight,this.camera,dt);
  for(const b of this.eye.bones)b.updateMatrixWorld(true);this.props.update(this.active.time,dt);
  this.root.traverse(o=>{if((o as THREE.SkinnedMesh).isSkinnedMesh)(o as THREE.SkinnedMesh).computeBoundingSphere();});
 }
 private visibility(){for(const [i,value] of Object.entries(this.defaults))this.vis.get(Number(i))!.visible=value;for(const tracks of [this.furniture?[]:this.idleTracks,this.tracks[this.active.getClip().name]||[]])for(const tr of tracks){let v=tr.keys[0]?.[1];for(const [t,state]of tr.keys){if(t>this.active.time+1e-6)break;v=state;}if(v!==undefined)this.vis.get(tr.node)!.visible=v;}}
 private mouth(){for(const {spec,map}of this.mouths){const events=spec.events[this.active.getClip().name]||[];const state=mouthTransform(spec,events,this.active.time,this.mouthLooped);map.repeat.x=state.flipped?-1:1;map.offset.set(state.x,state.y);this.mouthTile=state.tile;this.mouthFlipped=state.flipped;}}
 diagnostics(measureFace=false,measurePose=false){
  const face:Record<string,number[]>={};if(measureFace){this.root.traverse(o=>{if((o as THREE.Bone).isBone&&/eye|brow|blow|mouth|bone_prop/i.test(o.name))face[o.name]=[...o.position.toArray(),...o.quaternion.toArray(),...o.scale.toArray()];});for(const [i,o]of this.vis)face[`visible-${i}`]=[Number(o.visible)];}
  const size=measurePose?visiblePoseBounds(this.root,.003,false).getSize(new THREE.Vector3()).toArray():undefined;
  return {action:this.furniture?'idle':this.actionId,actionTime:this.active.time,shaderTime:this.active.time+this.ambientLoopOffset,mouthTile:this.mouthTile,mouthFlipped:this.mouthFlipped,particleStates:measurePose?this.particles.map(p=>p.diagnostics(this.camera)):undefined,mirrors:this.mirrors.map(m=>({name:m.mesh.name,visible:m.mesh.visible,side:m.material.side,hasMap:!!m.material.uniforms.uReflectionMap.value,diag:m.lastDiag})),outlineMeshes:this.outline?.meshes.length||0,mouthMaps:this.mouths.map(({spec,map})=>({material:spec.material,texture:map.uuid,offset:map.offset.toArray()})),orientation:[this.root.rotation.x,this.root.rotation.y,this.root.rotation.z],meshes:this.meshes,bones:this.bones,durations:Object.fromEntries([...this.actions].map(([id,a])=>[id,a.getClip().duration])),animations:[...this.actions.values()].map(a=>a.getClip().name),gaze:this.eye.diagnostics(),face,transition:{remaining:Math.max(0,this.fadeLeft),incoming:this.active.getEffectiveWeight(),outgoing:this.fading?.getEffectiveWeight()||0,props:this.props.meshes},...(size?{pose:{size,halo:this.halos[0]?.node.getWorldPosition(new THREE.Vector3()).toArray()||[],canvas:[],client:[innerWidth,innerHeight]}}:{})};
 }
 dispose(){if(this.disposed)return;this.disposed=true;this.depthTarget?.dispose();for(const m of this.mirrors)m.dispose();this.mirrors.length=0;this.outline?.dispose();this.mixer?.stopAllAction();if(this.mixer)this.mixer.uncacheRoot(this.root.children[0]);for(const s of this.skeletons)s.dispose();for(const g of this.geometries)g.dispose();for(const m of this.materials)m.dispose();for(const t of this.textures){const image=t.source.data;if(image?.close)image.close();t.dispose();}this.scene.clear();}
}
