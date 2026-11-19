import * as THREE from 'three';

// Sample the authored emitter pose without seeking the visible mixer. The
// desktop's framing/rotation is deliberately outside this source-world space.
export class ParticleTransforms {
 private defaults=new Map<THREE.Object3D,{position:THREE.Vector3;quaternion:THREE.Quaternion;scale:THREE.Vector3}>();
 private clips=new Map<string,{duration:number;tracks:Map<THREE.Object3D,Map<string,THREE.Interpolant>>}>();
 private cache=new Map<THREE.Object3D,THREE.Matrix4>();private key='';
 constructor(private root:THREE.Object3D,clips:THREE.AnimationClip[]){
  root.traverse(n=>this.refresh(n));
  for(const clip of clips){const tracks=new Map<THREE.Object3D,Map<string,THREE.Interpolant>>();
   for(const track of clip.tracks){const parsed=THREE.PropertyBinding.parseTrackName(track.name);if(!['position','quaternion','scale'].includes(parsed.propertyName))continue;
    const node=THREE.PropertyBinding.findNode(root,parsed.nodeName) as THREE.Object3D|null;if(!node)throw Error('粒子动画缺少节点：'+parsed.nodeName);
    if(!tracks.has(node))tracks.set(node,new Map());tracks.get(node)!.set(parsed.propertyName,(track as any).createInterpolant());
   }this.clips.set(clip.name,{duration:clip.duration,tracks});
  }
 }
 refresh(node:THREE.Object3D){this.defaults.set(node,{position:node.position.clone(),quaternion:node.quaternion.clone(),scale:node.scale.clone()});this.cache.clear();}
 matrix(node:THREE.Object3D,clipName:string,time:number):THREE.Matrix4{
  const clip=this.clips.get(clipName);time=THREE.MathUtils.clamp(time,0,clip?.duration??Infinity);
  const key=clipName+':'+time;if(key!==this.key){this.key=key;this.cache.clear();}
  const visit=(n:THREE.Object3D):THREE.Matrix4=>{
   if(n===this.root)return new THREE.Matrix4();const cached=this.cache.get(n);if(cached)return cached;
   const base=this.defaults.get(n)!;const position=base.position.clone(),quaternion=base.quaternion.clone(),scale=base.scale.clone();
   for(const [property,interpolant] of clip?.tracks.get(n)||[])({position,quaternion,scale}[property as 'position'|'quaternion'|'scale']).fromArray(interpolant.evaluate(time));
   const local=new THREE.Matrix4().compose(position,quaternion,scale),matrix=n.parent?visit(n.parent).clone().multiply(local):local;this.cache.set(n,matrix);return matrix;
  };return visit(node).clone();
 }
}
