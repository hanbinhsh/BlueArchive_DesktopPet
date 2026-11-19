import * as THREE from 'three';

// Match the wiki ModelViewer: area-weighted normals welded at 1e-4,
// back-facing hulls, black ink, and width = .002 * percentage / 100.
// Reference: https://zh.bluearchive.wiki/wiki/MediaWiki:Gadget-impl.js?action=raw
export function smoothOutlineNormals(geometry:THREE.BufferGeometry){
 if(geometry.hasAttribute('smoothNormal'))return;
 const p=geometry.getAttribute('position');if(!p)return;
 const keys:string[]=[],sums=new Map<string,THREE.Vector3>();
 for(let i=0;i<p.count;i++){
  const key=[p.getX(i),p.getY(i),p.getZ(i)].map(v=>Math.round(v*1e4)).join(',');
  keys.push(key);if(!sums.has(key))sums.set(key,new THREE.Vector3());
 }
 const index=geometry.index,count=index?.count??p.count,a=new THREE.Vector3(),b=new THREE.Vector3(),c=new THREE.Vector3();
 for(let i=0;i+2<count;i+=3){
  const ids=[0,1,2].map(k=>index?index.getX(i+k):i+k);
  a.fromBufferAttribute(p,ids[0]);b.fromBufferAttribute(p,ids[1]).sub(a);c.fromBufferAttribute(p,ids[2]).sub(a);b.cross(c);
  for(const id of ids)sums.get(keys[id])!.add(b);
 }
 for(const normal of sums.values())normal.normalize();
 const data=new Float32Array(p.count*3);for(let i=0;i<p.count;i++)sums.get(keys[i])!.toArray(data,i*3);
 geometry.setAttribute('smoothNormal',new THREE.BufferAttribute(data,3));
}

const vertexShader=`
#include <common>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <clipping_planes_pars_vertex>
attribute vec3 smoothNormal;
uniform float outlineWidth;
varying vec3 outlineWorld;
void main(){
 vec3 objectNormal=smoothNormal;
 #include <skinbase_vertex>
 #include <skinnormal_vertex>
 vec3 transformed=position;
 #include <morphtarget_vertex>
 #include <skinning_vertex>
 outlineWorld=(modelMatrix*vec4(transformed,1.)).xyz;
 vec4 mvPosition=modelViewMatrix*vec4(transformed,1.);
 vec3 viewNormal=normalize(normalMatrix*objectNormal);
 // Our orthographic camera uses the wiki's default 35-degree perspective
 // projection scale, giving the same screen-space width at equal viewport height.
 float depth=isOrthographic?3.171594802/projectionMatrix[1][1]:max(-mvPosition.z,.05);
 mvPosition.xyz+=viewNormal*outlineWidth*depth;
 gl_Position=projectionMatrix*mvPosition;
 #include <clipping_planes_vertex>
}`;

export class ModelOutline{
 readonly meshes:THREE.Mesh[]=[];
 private materials:THREE.ShaderMaterial[]=[];
 constructor(root:THREE.Object3D){
  const originals:THREE.Mesh[]=[];root.traverse(o=>{if((o as THREE.Mesh).isMesh&&!o.userData.BA_auxiliary)originals.push(o as THREE.Mesh);});
  for(const mesh of originals){
   const materials=Array.isArray(mesh.material)?mesh.material:[mesh.material];
   if(materials.some(m=>m.transparent||!m.colorWrite||m.userData.BA_stencil||m.userData.BA_mirrorSurface||m.userData.BA_cafeParticle||m.userData.BA_waterFx))continue;
   smoothOutlineNormals(mesh.geometry);if(!mesh.geometry.hasAttribute('smoothNormal'))continue;
   const clip=materials.find(m=>m.userData._BA_clipPlane)?.userData._BA_clipPlane;
   const clipStencil=materials.find(m=>m.userData.BA_clipStencil)?.userData.BA_clipStencil;
   const material=new THREE.ShaderMaterial({side:THREE.BackSide,clipping:true,uniforms:clip?{outlineWidth:{value:0},clipPlane:clip}:{outlineWidth:{value:0}},vertexShader,fragmentShader:clip?`#include <clipping_planes_pars_fragment>
uniform vec4 clipPlane;varying vec3 outlineWorld;
void main(){
 #include <clipping_planes_fragment>
 if(dot(clipPlane.xyz,outlineWorld)+clipPlane.w<0.)discard;
 gl_FragColor=vec4(0.,0.,0.,1.);
 #include <colorspace_fragment>
}`:`#include <clipping_planes_pars_fragment>
void main(){
 #include <clipping_planes_fragment>
 gl_FragColor=vec4(0.,0.,0.,1.);
 #include <colorspace_fragment>
}`});
   if(clipStencil){material.stencilWrite=true;material.stencilRef=clipStencil;material.stencilFunc=THREE.EqualStencilFunc;material.stencilZPass=THREE.KeepStencilOp;}
   let hull:THREE.Mesh;
   if((mesh as THREE.SkinnedMesh).isSkinnedMesh){const source=mesh as THREE.SkinnedMesh,skin=new THREE.SkinnedMesh(mesh.geometry,material);skin.bindMode=source.bindMode;skin.bind(source.skeleton,source.bindMatrix);hull=skin;}else hull=new THREE.Mesh(mesh.geometry,material);
   hull.name=mesh.name+'__outline';hull.userData.BA_auxiliary=true;hull.userData.isOutline=true;hull.frustumCulled=false;hull.renderOrder=-1;
   hull.morphTargetInfluences=mesh.morphTargetInfluences;hull.morphTargetDictionary=mesh.morphTargetDictionary;hull.visible=false;
   // Hulls are visual only; they must not enlarge picking or framing bounds.
   hull.raycast=()=>{};mesh.add(hull);this.meshes.push(hull);this.materials.push(material);
  }
 }
 apply(enabled:boolean,width:number){for(const mesh of this.meshes)mesh.visible=enabled&&width>0;for(const m of this.materials)m.uniforms.outlineWidth.value=.002*width/100;}
 dispose(){for(const mesh of this.meshes)mesh.removeFromParent();for(const m of this.materials)m.dispose();this.meshes.length=this.materials.length=0;}
}
