import * as THREE from 'three';
import {unityCurve,particleColor} from './cafe-particles';
import {ParticleTransforms} from './particle-transforms';

// Restricted to the exporter-validated stationary local emitter case. Sampling
// the authored pose makes ribbons seekable and independent of frame rate.
export class CafeTrail {
 private positions=new THREE.BufferAttribute(new Float32Array(130*3),3);
 private colors=new THREE.BufferAttribute(new Float32Array(130*4),4);
 constructor(private mesh:THREE.Mesh,private material:THREE.MeshBasicMaterial,private emitter:THREE.Object3D,private root:THREE.Object3D,private transforms:ParticleTransforms){
  const g=mesh.geometry;g.setAttribute('position',this.positions);g.setAttribute('color',this.colors);
  const indices:number[]=[];for(let i=0;i<64;i++){const a=i*2;indices.push(a,a+1,a+2,a+1,a+3,a+2);}g.setIndex(indices);g.setDrawRange(0,0);
  material.vertexColors=true;material.depthWrite=false;material.side=THREE.DoubleSide;material.needsUpdate=true;
  const s=material.userData.BA_cafeTrail.spec;mesh.renderOrder=(s.material.queue>=0?s.material.queue:3000)*1e6+(s.renderer.m_SortingOrder||0)*1e4-(s.renderer.m_SortingFudge||0);
  mesh.frustumCulled=false;mesh.userData.BA_auxiliary=true;
 }
 update(time:number,clip:string,camera:THREE.Camera){
  const info=this.material.userData.BA_cafeTrail,s=info.spec,c=s.control,p=s.particle,trail=info.trail;
  const life=unityCurve(p.InitialModule.startLifetime,s.initialTime||0),birth=unityCurve(s.delay,0)+s.burst;
  const speed=c.speed*(s.simulationSpeed??1),age=((time-c.start)*c.speed+c.clipIn)*(s.simulationSpeed??1)-birth;
  const span=unityCurve(trail.lifetime,0)*life,last=Math.min(age,life),first=Math.max(0,age-span);
  this.mesh.visible=clip===s.clip&&time>=c.start&&time<c.start+c.duration&&age>=0&&last>first&&(!trail.dieWithParticles||age<life);
  this.mesh.geometry.setDrawRange(0,0);if(!this.mesh.visible)return;
  const timeline=(a:number)=>c.start+((birth+a)/(s.simulationSpeed??1)-c.clipIn)/c.speed;
  const inverse=this.transforms.matrix(this.emitter,clip,time).invert();
  const direction=camera.getWorldDirection(new THREE.Vector3()).transformDirection(this.root.matrixWorld.clone().invert());
  const count=Math.min(64,Math.max(2,Math.ceil((last-first)/speed*60)));
  const points=Array.from({length:count+1},(_,i)=>new THREE.Vector3().applyMatrix4(this.transforms.matrix(this.emitter,clip,timeline(last-(last-first)*i/count))));
  const global=particleColor(trail.colorOverLifetime,THREE.MathUtils.clamp(age/life,0,1)),tint=info.material.colors._Color||[1,1,1,1],multiply=info.material.floats._Multiply??1;
  for(let i=0;i<=count;i++){
   const fraction=i/count,tangent=points[Math.min(count,i+1)].clone().sub(points[Math.max(0,i-1)]);
   const side=new THREE.Vector3().crossVectors(tangent,direction).normalize().multiplyScalar(unityCurve(trail.widthOverTrail,fraction)*.5);
   const rgba=particleColor(trail.colorOverTrail,fraction),rgb=new THREE.Color().setRGB(...rgba.slice(0,3).map((v,k)=>v*global[k])as[number,number,number]);
   if(s.renderer.m_ApplyActiveColorSpace)rgb.convertSRGBToLinear();rgb.multiply(new THREE.Color().setRGB(tint[0]*multiply,tint[1]*multiply,tint[2]*multiply));
   for(let j=0;j<2;j++){
    const q=points[i].clone().addScaledVector(side,j?1:-1).applyMatrix4(inverse);this.positions.setXYZ(i*2+j,q.x,q.y,q.z);
    this.colors.setXYZW(i*2+j,rgb.r,rgb.g,rgb.b,THREE.MathUtils.clamp(rgba[3]*global[3]*tint[3]*multiply,0,1));
   }
  }
  this.positions.needsUpdate=true;this.colors.needsUpdate=true;this.mesh.geometry.setDrawRange(0,count*6);
 }
}
