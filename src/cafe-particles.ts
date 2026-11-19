import * as THREE from 'three';
import {ParticleTransforms} from './particle-transforms';

export function unityCurve(c:any,t:number,random=.5):number{
 if(!c)return 0;
 const evalCurve=(v:any)=>{
  let curveTime=t;
  const keys=v?.m_Curve||[];if(!keys.length)return 0;
  const first=keys[0].time,last=keys.at(-1).time,span=last-first;
  if(span>0&&(curveTime<first||curveTime>last)){
   const wrap=curveTime<first?v.m_PreInfinity:v.m_PostInfinity;
   if(wrap===1)curveTime=first+((curveTime-first)%span+span)%span;
   else if(wrap===0){const phase=((curveTime-first)%(2*span)+2*span)%(2*span);curveTime=first+(phase>span?2*span-phase:phase);}
  }
  if(curveTime<=keys[0].time)return keys[0].value;
  for(let i=1;i<keys.length;i++)if(curveTime<keys[i].time){
   const a=keys[i-1],b=keys[i],d=b.time-a.time,u=(curveTime-a.time)/d;
   if(!Number.isFinite(a.outSlope)||!Number.isFinite(b.inSlope))return a.value;
   return (2*u*u*u-3*u*u+1)*a.value+(u*u*u-2*u*u+u)*d*a.outSlope+(-2*u*u*u+3*u*u)*b.value+(u*u*u-u*u)*d*b.inSlope;
  }return keys.at(-1).value;
 };
 switch(c.minMaxState){case 1:return c.scalar*evalCurve(c.maxCurve);case 2:return THREE.MathUtils.lerp(c.minScalar*evalCurve(c.minCurve),c.scalar*evalCurve(c.maxCurve),random);case 3:return THREE.MathUtils.lerp(c.minScalar,c.scalar,random);default:return c.scalar??0;}
}
// Stable per-property samples make seeking, pause and playback-speed changes
// reproducible. This is not a claim to reproduce Unity's private RNG bitwise.
export function particleRandom(seed:number,key:string){let h=seed>>>0;for(let i=0;i<key.length;i++)h=Math.imul(h^key.charCodeAt(i),16777619);h=Math.imul(h^(h>>>16),0x21f0aaad);h=Math.imul(h^(h>>>15),0x735a2d97);return ((h^(h>>>15))>>>0)/4294967296;}
function gradient(g:any,t:number){
 const channel=(alpha:boolean)=>{
  const count=g?.[alpha?'m_NumAlphaKeys':'m_NumColorKeys']||0;if(!count)return alpha?[1]:[1,1,1];
  let prev=0;for(let i=1;i<count;i++){if(t*65535<g[`${alpha?'a':'c'}time${i}`])break;prev=i;}
  const a=g[`key${prev}`],b=g[`key${Math.min(prev+1,count-1)}`],ta=g[`${alpha?'a':'c'}time${prev}`]/65535,tb=g[`${alpha?'a':'c'}time${Math.min(prev+1,count-1)}`]/65535;
  const w=g.m_Mode===1?0:THREE.MathUtils.clamp((t-ta)/(tb-ta||1),0,1);
  return (alpha?['a']:['r','g','b']).map(k=>THREE.MathUtils.lerp(a[k],b[k],w));
 };return [...channel(false),...channel(true)];
}
export function particleColor(c:any,t:number,r=.5){if(!c)return [1,1,1,1];if(c.minMaxState===1)return gradient(c.maxGradient,t);if(c.minMaxState===4)return gradient(c.maxGradient,r);if(c.minMaxState===3){const a=gradient(c.minGradient,t),b=gradient(c.maxGradient,t);return a.map((v,k)=>THREE.MathUtils.lerp(v,b[k],r));}const a=c.maxColor;return ['r','g','b','a'].map(k=>c.minMaxState===2?THREE.MathUtils.lerp(c.minColor[k],a[k],r):a[k]);}
const color=particleColor;

export function particleShape(shape:any,seed:number,ordinal=0,count=1,emissionTime=0,period=1){
 const position=new THREE.Vector3(),direction=new THREE.Vector3(0,0,1);if(!shape?.enabled)return {position,direction};
 const r=(key:string)=>particleRandom(seed,key);
 // Animated arcs use revolutions per second (Unity ShapeModule.arcSpeed).
 const arcAngle=()=>{const arc=shape.arc.value*Math.PI/180;if(arc<=0)return 0;
  if(shape.arc.mode===3)return ordinal/Math.max(1,count)*arc;
  if(shape.arc.mode===1||shape.arc.mode===2){const steps=Math.max(1,Math.ceil(Math.abs(emissionTime)*60));let turns=0;for(let n=0;n<steps;n++)turns+=unityCurve(shape.arc.speed,(((n+.5)*emissionTime/steps/period)%1+1)%1,r('arcSpeed'))*emissionTime/steps;const span=shape.arc.mode===2?arc*2:arc,phase=((turns*Math.PI*2)%span+span)%span;return shape.arc.mode===2&&phase>arc?span-phase:phase;}
  return r('arc')*arc;
 };
 if(shape.type===5)position.set(r('shapeX')-.5,r('shapeY')-.5,r('shapeZ')-.5);
 if(shape.type===16){
  const lengths=['x','y','z'].map(k=>Math.abs(shape.m_Scale[k])),pick=r('edgeAxis')*lengths.reduce((a,b)=>a+b,0);
  const axis=pick<lengths[0]?0:pick<lengths[0]+lengths[1]?1:2;
  position.set(...[0,1,2].map(k=>k===axis?r('edgePosition')-.5:r('edgeSide'+k)<.5?-.5:.5) as [number,number,number]);
 }
 if(shape.type===12)position.x=(r('edge')*2-1)*shape.radius.value;
 if(shape.type===0||shape.type===2){const z=shape.type===2?r('sphereZ'):2*r('sphereZ')-1,angle=r('sphereAngle')*Math.PI*2,xy=Math.sqrt(1-z*z);direction.set(xy*Math.cos(angle),xy*Math.sin(angle),z);const inner=1-shape.radiusThickness;position.copy(direction).multiplyScalar(shape.radius.value*Math.cbrt(THREE.MathUtils.lerp(inner**3,1,r('radius'))));}
 if(shape.type===10||shape.type===4||shape.type===8){const angle=arcAngle();const inner=1-shape.radiusThickness,radius=shape.radius.value*Math.sqrt(THREE.MathUtils.lerp(inner*inner,1,r('radius')));direction.set(Math.cos(angle),Math.sin(angle),0);position.copy(direction).multiplyScalar(radius);if(shape.type===4||shape.type===8){const cone=shape.angle*Math.PI/180,radial=shape.radius.value?radius/shape.radius.value:0;if(shape.type===8){const slope=Math.tan(cone),r0=shape.radius.value,r1=r0+shape.length*slope,rz=Math.cbrt(THREE.MathUtils.lerp(r0**3,r1**3,r('coneVolume'))),z=Math.abs(slope)>1e-7?(rz-r0)/slope:r('coneVolume')*shape.length;position.copy(direction).multiplyScalar(rz*radial).setZ(z);}direction.multiplyScalar(Math.sin(cone)*radial).setZ(Math.cos(cone)).normalize();}}
 if(shape.randomPositionAmount){const z=2*r('positionZ')-1,theta=r('positionAngle')*Math.PI*2,radius=shape.randomPositionAmount*Math.cbrt(r('positionRadius')),xy=Math.sqrt(1-z*z);position.add(new THREE.Vector3(xy*Math.cos(theta),xy*Math.sin(theta),z).multiplyScalar(radius));}
 if(shape.sphericalDirectionAmount&&position.lengthSq()>1e-12)direction.lerp(position.clone().normalize(),shape.sphericalDirectionAmount).normalize();
 if(shape.randomDirectionAmount){const z=2*r('directionZ')-1,theta=r('directionAngle')*Math.PI*2,xy=Math.sqrt(1-z*z);direction.lerp(new THREE.Vector3(xy*Math.cos(theta),xy*Math.sin(theta),z),shape.randomDirectionAmount).normalize();}
 const q=new THREE.Quaternion().setFromEuler(new THREE.Euler(shape.m_Rotation.x*Math.PI/180,shape.m_Rotation.y*Math.PI/180,shape.m_Rotation.z*Math.PI/180,'YXZ'));
 position.multiply(new THREE.Vector3(shape.m_Scale.x,shape.m_Scale.y,shape.m_Scale.z)).applyQuaternion(q).add(new THREE.Vector3(shape.m_Position.x,shape.m_Position.y,shape.m_Position.z));direction.applyQuaternion(q);return {position,direction};
}

// Unity ring buffers retain particles beyond their ordinary lifetime.
export function particleAge(age:number,life:number,mode:number,range={x:0,y:1}){
 if(age<0)return age;
 if(mode===1)return Math.min(age,life-1e-7);
 if(mode===2){const lo=life*range.x,hi=life*range.y;if(age>=hi&&hi>lo)return lo+(age-hi)%(hi-lo);}
 return age;
}

function safeSource(spec:any){return spec.sourceName||'';}
export class CafeParticle{
 get name(){return this.mesh.name;}
 // Sub-emitter events use this same deterministic integration as visible
 // particles, including sampled lifetime and shape origin. They are evaluated
 // once when the scene is linked, so seeking cannot spawn duplicate children.
 emissionState(event:number){
  const c=this.spec.control,age=event===2?this.life:0;
  this.update(c.start,this.spec.clip,undefined,age);
  const i=this.spec.particle.InitialModule,over=this.spec.particle.ColorModule;
  const startColor=color(i.startColor,this.initialTime,this.randoms.get(i.startColor)),endColor=over?.enabled?color(over.gradient,age/this.life,this.randoms.get(over.gradient)):[1,1,1,1];
  return {time:c.start+((this.birth+age)/(this.spec.simulationSpeed??1)-c.clipIn)/c.speed,
   position:this.mesh.position.clone(),rotation:this.mesh.rotation.clone(),size:this.mesh.scale.clone(),color:startColor.map((v,k)=>v*endColor[k]*this.inheritedColor[k])};
 }
 startAt(time:number){const c=this.spec.control;c.clipIn=(c.start-time)*c.speed;this.integrate();}
 inheritFrom(event:ReturnType<CafeParticle['emissionState']>,properties:number){
  if(properties&1)this.inheritedColor=event.color;
  if(properties&2)this.inheritedSize=event.size;
  if(properties&4)this.inheritedRotation=event.rotation;
 }
 private inheritedColor=[1,1,1,1];private inheritedSize?:THREE.Vector3;private inheritedRotation?:THREE.Euler;
 private map?:THREE.Texture;private spec:any;private velocity:number[][]=[];private angles:number[][]=[];private life=1;private birth=0;private samples=0;
 private initialTime=0;
 private origin=new THREE.Vector3();private initialVelocity=new THREE.Vector3();private direction=new THREE.Vector3(0,0,1);private randoms=new WeakMap<object,number>();private integrationRate=30;
 private sample(c:any,t:number){return unityCurve(c,t,(c&&this.randoms.get(c))??.5);}
 constructor(private mesh:THREE.Mesh,private material:THREE.MeshBasicMaterial,textures:Set<THREE.Texture>,private sourceRoot?:THREE.Object3D,private transforms?:ParticleTransforms){
  this.spec=material.userData.BA_cafeParticle;const s=this.spec,p=s.particle,i=p.InitialModule;
  const register=(value:any,path:string)=>{if(!value||typeof value!=='object')return;if('minMaxState'in value)this.randoms.set(value,s.seed===undefined?.5:particleRandom(s.seed,path));for(const [k,v]of Object.entries(value))register(v,path+'.'+k);};register(p,'particle');register(s.delay,'delay');
  // Main-module curves are sampled at emission time, not at particle age zero.
  // Airi's moving note emitter has a zero speed only at the start of its cycle.
  const period=s.emissionPeriod||s.period||1;this.initialTime=s.initialTime??((s.burst%period+period)%period)/period;
  const shape=particleShape(p.ShapeModule,s.seed||0,s.ordinal,s.burstCount,s.burst,s.period||1);this.origin.copy(shape.position);this.direction.copy(shape.direction);this.initialVelocity.copy(shape.direction).multiplyScalar(this.sample(i.startSpeed,this.initialTime));
  this.life=Math.max(.0001,this.sample(i.startLifetime,this.initialTime));this.birth=this.sample(s.delay,0)+s.burst;
  const clamp=p.ClampVelocityModule,v=p.VelocityModule,hasOrbit=v?.enabled&&['orbitalX','orbitalY','orbitalZ','radial'].some(k=>v[k]?.scalar||v[k]?.minScalar);this.integrationRate=clamp?.enabled||i.gravityModifier?.scalar||hasOrbit?60:30;
  this.integrate();
  if(material.map){this.map=material.map.clone();material.map=this.map;textures.add(this.map);}
  mesh.frustumCulled=false;mesh.userData.BA_auxiliary=true;
  // Preserve timeline layering for coplanar screen sprites. Original queue
  // remains the primary order; stable scene traversal breaks equal-queue ties.
  const queue=s.material.queue>=0?s.material.queue:s.surfaceTint?2000:3000;
  mesh.renderOrder=queue*1e6+(s.renderer?.m_SortingOrder||0)*1e4-(s.renderer?.m_SortingFudge||0);
  material.depthWrite=material.userData.BA_depthWrite===true;
  // The original FX meshes use slope bias to separate foam from the surface
  // beneath it. Dropping it makes the two layers fight as the camera rotates.
  const depthFactor=s.material.floats._ZOffsetFactor||0,depthUnits=s.material.floats._ZOffsetUnits||0;
  material.polygonOffset=depthFactor!==0||depthUnits!==0;
  material.polygonOffsetFactor=depthFactor;material.polygonOffsetUnits=depthUnits;
  const shader=s.material.shader;
  // Local screen billboards retain the reflected source quad winding.
  // Honor authored culling so scanline planes cannot show through the back
  // of a cabinet when the scene is rotated.
  if(s.renderer?.m_RenderMode===0&&s.renderer.m_RenderAlignment===2){
   const cull=s.material.floats._Cull_Mode;
   if(cull===2)material.side=THREE.BackSide;
   else if(cull===1)material.side=THREE.FrontSide;
  }
  if(shader.includes('Add')&&s.material.floats._DstBlend===1){material.blending=THREE.AdditiveBlending;}
 }
 diagnostics(camera:THREE.Camera){const p=this.mesh.getWorldPosition(new THREE.Vector3()),bounds=new THREE.Box3(),v=new THREE.Vector3(),positions=this.mesh.geometry.getAttribute('position');for(let i=0;i<positions.count;i++)bounds.expandByPoint(v.fromBufferAttribute(positions,i).applyMatrix4(this.mesh.matrixWorld).project(camera));return {name:this.mesh.name,source:safeSource(this.spec),parent:this.mesh.parent?.name,visible:this.mesh.visible,opacity:this.material.opacity,scale:this.mesh.getWorldScale(new THREE.Vector3()).toArray(),position:p.toArray(),screen:p.project(camera).toArray(),screenBounds:[bounds.min.toArray(),bounds.max.toArray()]};}
 private birthMatrix=new THREE.Matrix4();
 private timelineTime(age:number){const s=this.spec,c=s.control;return c.start+((this.birth+age)/(s.simulationSpeed??1)-c.clipIn)/c.speed;}
 private sourceMatrix(time:number){
  if(this.transforms)return this.transforms.matrix(this.mesh.parent!,this.spec.clip,time);
  this.mesh.parent?.updateWorldMatrix(true,false);this.sourceRoot?.updateWorldMatrix(true,false);
  return new THREE.Matrix4().copy(this.sourceRoot?.matrixWorld||new THREE.Matrix4()).invert().multiply(this.mesh.parent?.matrixWorld||new THREE.Matrix4());
 }
 private integrate(){
  const mesh=this.mesh,s=this.spec,p=s.particle,i=p.InitialModule,v=p.VelocityModule,clamp=p.ClampVelocityModule;
  const hasOrbit=v?.enabled&&['orbitalX','orbitalY','orbitalZ','radial'].some(k=>v[k]?.scalar||v[k]?.minScalar);
  this.birthMatrix=this.sourceMatrix(this.timelineTime(0));
  const world=s.simulationSpace===1,hasGravity=!!(i.gravityModifier?.scalar||i.gravityModifier?.minScalar);
  const simulationMatrix=(age:number)=>world?this.birthMatrix:this.sourceMatrix(this.timelineTime(age));
  const convertWorld=(vector:THREE.Vector3,age:number)=>{vector.x*=-1;vector.applyMatrix3(new THREE.Matrix3().setFromMatrix4(simulationMatrix(age).clone().invert()));vector.x*=-1;return vector;};
  const moduleVelocity=(u:number)=>{
   const result=new THREE.Vector3(...[0,1,2].map(a=>v?.enabled?this.sample(v[['x','y','z'][a]],u):0) as [number,number,number]);
   if(v?.inWorldSpace)return convertWorld(result,u*this.life);
   if(world&&v?.enabled){result.x*=-1;result.applyMatrix3(new THREE.Matrix3().setFromMatrix4(this.birthMatrix.clone().invert().multiply(this.sourceMatrix(this.timelineTime(u*this.life)))));result.x*=-1;}
   return result;
  };
  this.samples=Math.ceil(this.life*this.integrationRate);this.velocity=[[0,0,0]];this.angles=[[0,0,0]];
  let previousModule=moduleVelocity(0),motion=this.initialVelocity.clone().add(previousModule);
  for(let k=1;k<=this.samples;k++){
   const age=Math.min(this.life,k/this.integrationRate),u=age/this.life,dt=Math.min(1/this.integrationRate,this.life-(k-1)/this.integrationRate),before=motion.clone().multiplyScalar(v?.enabled?this.sample(v.speedModifier,(age-dt)/this.life):1),currentModule=moduleVelocity(u),r=p.RotationModule;
   motion.add(currentModule).sub(previousModule);if(hasGravity)motion.addScaledVector(convertWorld(new THREE.Vector3(0,-9.8100004196167,0),age-dt/2),this.sample(i.gravityModifier,u)*dt);previousModule.copy(currentModule);
   if(clamp?.enabled){let speed=motion.length(),limit=Math.max(0,this.sample(clamp.magnitude,u));if(speed>limit)motion.multiplyScalar(THREE.MathUtils.lerp(speed,limit,clamp.dampen)/speed);speed=motion.length();let drag=this.sample(clamp.drag,u);if(clamp.multiplyDragByParticleVelocity)drag*=speed;if(clamp.multiplyDragByParticleSize)drag*=this.sample(i.startSize,this.initialTime);motion.multiplyScalar(Math.max(0,1-drag*dt));}
   const position=new THREE.Vector3(...this.velocity[k-1]).addScaledVector(before.clone().add(motion.clone().multiplyScalar(v?.enabled?this.sample(v.speedModifier,u):1)),.5*dt);
   if(hasOrbit){
    const center=new THREE.Vector3(...['orbitalOffsetX','orbitalOffsetY','orbitalOffsetZ'].map(k=>this.sample(v[k],u)) as [number,number,number]),relative=position.clone().add(this.origin).sub(center);
    relative.applyEuler(new THREE.Euler(...['orbitalX','orbitalY','orbitalZ'].map(k=>this.sample(v[k],u)*dt) as [number,number,number],'YXZ'));
    const radius=relative.length();if(radius>1e-8)relative.multiplyScalar(Math.max(0,radius+this.sample(v.radial,u)*dt)/radius);
    position.copy(relative).add(center).sub(this.origin);
   }
   this.velocity.push(position.toArray());
   this.angles.push(this.angles[k-1].map((x,a)=>x+(r?.enabled?(r.separateAxes?this.sample(r[['x','y','curve'][a]],u):a===2?this.sample(r.curve,u):0):0)*dt));
  }
 }
 update(time:number,clip:string,camera?:THREE.Camera,sampleAge?:number,ambientTime=time){
  const s=this.spec,c=s.control,p=s.particle,i=p.InitialModule;
  if(s.persistent)time=ambientTime;
  let age=((time-c.start)*c.speed+c.clipIn)*(s.simulationSpeed??1)-this.birth;
  if(s.loop&&age>=0)age%=s.period;
  age=particleAge(age,this.life,s.ringMode,s.ringRange);
  if(sampleAge!==undefined)age=Math.min(sampleAge,this.life);
  const alive=clip===s.clip&&time>=c.start&&(s.persistent||time<c.start+c.duration)&&age>=0&&age<this.life;
  // Hidden Unity renderers still simulate and trigger their sub-emitters.
  this.mesh.visible=alive&&s.renderer?.m_Enabled!==false;if(!alive&&sampleAge===undefined)return;
  for(const track of s.propertyTracks||[]){
   const clock=s.propertyClock||c;
   const t=(time-clock.start)*clock.speed+clock.clipIn;let hi=track.times.findIndex((v:number)=>v>t);if(hi<0)hi=track.times.length;const lo=Math.max(0,hi-1),end=Math.min(hi,track.times.length-1);
   const w=THREE.MathUtils.clamp((t-track.times[lo])/(track.times[end]-track.times[lo]||1),0,1),value=THREE.MathUtils.lerp(track.values[lo],track.values[end],w);
   for(const target of [s.material,this.material.userData.BA_waterFx,this.material.userData.BA_smokeFx]){
    if(!target?.[track.category])continue;
    if(track.component===null)target[track.category][track.property]=value;
    else if(target[track.category][track.property])target[track.category][track.property][track.component]=value;
   }
  }
  const u=age/this.life,frame=Math.min(this.samples,Math.floor(age*this.integrationRate)),next=Math.min(this.samples,frame+1);
  const sampleStart=Math.min(this.life,frame/this.integrationRate),sampleEnd=Math.min(this.life,next/this.integrationRate),weight=sampleEnd>sampleStart?(age-sampleStart)/(sampleEnd-sampleStart):0;
  const integrated=(table:number[][])=>table[frame].map((v,a)=>THREE.MathUtils.lerp(v,table[next][a],weight));
  const v=integrated(this.velocity),a=integrated(this.angles);
  this.mesh.position.copy(this.origin).add(new THREE.Vector3(...v));this.mesh.position.x*=-1;
  this.mesh.rotation.set((i.rotation3D?this.sample(i.startRotationX,this.initialTime):0)+a[0],-((i.rotation3D?this.sample(i.startRotationY,this.initialTime):0)+a[1]),-(this.sample(i.startRotation,this.initialTime)+a[2]),'YXZ');
  if(this.inheritedRotation){this.mesh.rotation.x+=this.inheritedRotation.x;this.mesh.rotation.y+=this.inheritedRotation.y;this.mesh.rotation.z+=this.inheritedRotation.z;}
  let relative:THREE.Matrix4|undefined;
  if(s.simulationSpace===1){
   let current:THREE.Matrix4;
   if(sampleAge!==undefined)current=this.sourceMatrix(this.timelineTime(age));
   else{this.mesh.parent!.updateWorldMatrix(true,false);this.sourceRoot?.updateWorldMatrix(true,false);current=new THREE.Matrix4().copy(this.sourceRoot?.matrixWorld||new THREE.Matrix4()).invert().multiply(this.mesh.parent!.matrixWorld);}
   relative=current.invert().multiply(this.birthMatrix);this.mesh.position.applyMatrix4(relative);
  }
  if(s.renderer?.m_RenderAlignment===4||p.ShapeModule?.alignToDirection){const direction=this.direction.clone();direction.x*=-1;this.mesh.quaternion.premultiply(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,0,1),direction));}
  if(relative&&s.renderer?.m_RenderAlignment!==1)this.mesh.quaternion.premultiply(new THREE.Quaternion().setFromRotationMatrix(relative.clone().extractRotation(relative)));
  if(s.renderer?.m_RenderMode===2){
   const parent=this.mesh.parent!.getWorldQuaternion(new THREE.Quaternion()).invert();
   const world=this.sourceRoot?.getWorldQuaternion(new THREE.Quaternion())||new THREE.Quaternion();
   this.mesh.quaternion.copy(parent).multiply(world)
    .multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1,0,0),-Math.PI/2))
    .multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,1),-(this.sample(i.startRotation,this.initialTime)+a[2])));
  }
  if((camera||s.renderer?.m_RenderAlignment===1)&&[0,4].includes(s.renderer?.m_RenderMode)&&[0,1,3].includes(s.renderer.m_RenderAlignment)){
   const authored=this.mesh.quaternion.clone(),q=new THREE.Quaternion();this.mesh.parent!.updateWorldMatrix(true,false);this.mesh.parent!.getWorldQuaternion(q).invert();
   if(s.renderer.m_RenderAlignment===1&&this.sourceRoot){
    q.multiply(this.sourceRoot.getWorldQuaternion(new THREE.Quaternion()));
   }else if(camera&&s.renderer.m_RenderAlignment!==1){
    // Source billboards face +Z in Unity's camera frame. Three cameras look
    // down -Z; the reflected source geometry therefore needs a Y half-turn.
    // Omitting this mirrors glyphs and puts negative depth pivots behind heads.
    q.multiply(camera.getWorldQuaternion(new THREE.Quaternion()));
   }
   // Mesh particles apply their full 3D Euler rotation in the camera frame.
   // Unlike sprite roll, the camera's half-turn precedes that rotation.
   if(s.renderer.m_RenderMode===4&&s.renderer.m_RenderAlignment!==1){
    this.mesh.quaternion.copy(q).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),Math.PI)).multiply(authored);
   }else this.mesh.quaternion.copy(q).multiply(authored);
   // Apply the geometry's handedness conversion after the authored rotation.
   // Putting it before rotation reverses clockwise roll and pivot placement.
   if(s.renderer.m_RenderMode!==4&&s.renderer.m_RenderAlignment!==1)this.mesh.quaternion.multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),Math.PI));
  }
  const size=p.SizeModule,base=this.sample(i.startSize,this.initialTime);
  this.mesh.scale.set(...[0,1,2].map(axis=>(i.size3D?this.sample(i[['startSize','startSizeY','startSizeZ'][axis]],this.initialTime):base)*(size?.enabled?this.sample(size.separateAxes?size[['curve','y','z'][axis]]:size.curve,u):1)) as [number,number,number]);
  if(this.inheritedSize)this.mesh.scale.multiply(this.inheritedSize);
  // Unity BakeMesh confirms that View uses the opposite depth-pivot sign
  // from Facing/Local. The handedness turn above is still needed for UVs,
  // but must not bring authored background glows in front of the character.
  if(camera&&s.renderer?.m_RenderMode===0&&s.renderer.m_RenderAlignment===0){
   if(!this.mesh.geometry.boundingBox)this.mesh.geometry.computeBoundingBox();
   const pivot=this.mesh.geometry.boundingBox!.getCenter(new THREE.Vector3());
   this.mesh.position.add(new THREE.Vector3(0,0,-2*pivot.z*this.mesh.scale.z).applyQuaternion(this.mesh.quaternion));
  }
  if(camera&&s.renderer?.m_RenderMode===1){
   const velocity=new THREE.Vector3(...this.velocity[next].map((v,k)=>(v-this.velocity[frame][k])*this.integrationRate));velocity.x*=-1;
   const speed=velocity.length();if(relative)velocity.applyMatrix3(new THREE.Matrix3().setFromMatrix4(relative));
   this.mesh.parent!.updateWorldMatrix(true,false);velocity.transformDirection(this.mesh.parent!.matrixWorld);
   const cq=camera.getWorldQuaternion(new THREE.Quaternion()),right=new THREE.Vector3(1,0,0).applyQuaternion(cq),up=new THREE.Vector3(0,1,0).applyQuaternion(cq),x=velocity.dot(right),y=velocity.dot(up);
   // Unity's stretched sprite maps texture U along motion. Aligning V here
   // turned asymmetrical sigh/arrow textures sideways relative to their path.
   const angle=Math.abs(x)+Math.abs(y)>1e-6?Math.atan2(y,x):this.mesh.rotation.z;
   this.mesh.quaternion.copy(this.mesh.parent!.getWorldQuaternion(new THREE.Quaternion()).invert()).multiply(cq).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,1),angle));
   const width=this.mesh.scale.x;
   this.mesh.scale.x=this.mesh.scale.y*s.renderer.m_LengthScale+speed*(s.renderer.m_VelocityScale||0);
   this.mesh.scale.y=width;
   // Unity defines the renderer pivot on its original X/Y sprite axes even
   // though stretched UV U runs along velocity. Move the longitudinal Y
   // pivot to our U axis too; otherwise nozzle flames shift across the jet.
   if(!this.mesh.geometry.boundingBox)this.mesh.geometry.computeBoundingBox();
   const pivot=this.mesh.geometry.boundingBox!.getCenter(new THREE.Vector3());
   this.mesh.position.add(new THREE.Vector3(pivot.y-pivot.x-.5,-pivot.x-pivot.y,-pivot.z).multiply(this.mesh.scale).applyQuaternion(this.mesh.quaternion));
   // Native BakeMesh: zero pivot anchors U=0 at the particle, U=1 trails it;
   // Y shifts along length, X across width, and stretched sprites ignore Z.
  }
  if(relative)this.mesh.scale.multiply(new THREE.Vector3().setFromMatrixScale(relative));
  const flip=s.renderer?.m_Flip;if(flip){
   // Renderer flips mirror the sprite around its geometric centre. A source
   // pivot offset stays on the same side; reflecting it moves icons out of
   // their bubbles (notably the double-flipped credit-card sprites).
   const before=this.mesh.scale.clone();
   for(const axis of ['x','y','z'] as const)if(particleRandom(s.seed||0,'flip'+axis)<flip[axis])this.mesh.scale[axis]*=-1;
   if([0,1].includes(s.renderer.m_RenderMode)){
    if(!this.mesh.geometry.boundingBox)this.mesh.geometry.computeBoundingBox();
    const pivot=this.mesh.geometry.boundingBox!.getCenter(new THREE.Vector3());
    this.mesh.position.add(pivot.multiply(before.sub(this.mesh.scale)).applyQuaternion(this.mesh.quaternion));
   }
  }
  const initial=color(i.startColor,this.initialTime,this.randoms.get(i.startColor)),over=p.ColorModule?.enabled?color(p.ColorModule.gradient,u,this.randoms.get(p.ColorModule.gradient)):[1,1,1,1];
  for(let k=0;k<4;k++)initial[k]*=this.inheritedColor[k];
  if(this.material.userData.BA_smokeFx||this.material.userData.BA_waterFx){this.material.userData.BA_customData=[0,1].map(group=>[0,1,2,3].map(axis=>p.CustomDataModule?.enabled&&p.CustomDataModule[`mode${group}`]!==0?(p.CustomDataModule[`mode${group}`]===2?color(p.CustomDataModule[`color${group}`],u,this.randoms.get(p.CustomDataModule[`color${group}`]))[axis]:this.sample(p.CustomDataModule[`vector${group}_${axis}`],u)):0));}
  const tint=s.surfaceTint||(this.material.userData.BA_smokeFx?[1,1,1,1]:s.material.colors._Color||s.material.colors._Main_Color||[1,1,1,1]),multiply=s.surfaceTint||this.material.userData.BA_smokeFx?1:s.material.floats._Multiply??1;
  this.material.color.setRGB(...[0,1,2].map(k=>initial[k]*over[k]) as [number,number,number]);if(s.renderer?.m_ApplyActiveColorSpace)this.material.color.convertSRGBToLinear();this.material.color.multiply(new THREE.Color().setRGB(tint[0]*multiply,tint[1]*multiply,tint[2]*multiply));this.material.opacity=THREE.MathUtils.clamp(initial[3]*over[3]*multiply*(s.surfaceTint?tint[3]:1),0,1);
  const sheet=p.UVModule;if(sheet?.enabled){const nx=sheet.tilesX,ny=sheet.tilesY,total=nx*ny,f=Math.floor((((this.sample(sheet.startFrame,0)+this.sample(sheet.frameOverTime,u)*sheet.cycles)%1)+1)%1*total);this.material.userData.BA_uvFrame=[1/nx,1/ny,(f%nx)/nx,1-(Math.floor(f/nx)+1)/ny];}
  if(this.map){
   const tex=s.texture,st=tex?.scale||[1,1],off=tex?.offset||[0,0],uv=p.UVModule;
   let sx=st[0],sy=st[1],ox=off[0],oy=off[1];
   // AlphaBlend_0 adds the particle's first custom-data XY to source UVs.
   if(s.material.shader==='DSFX/FX_SHADER_AlphaBlend_0'&&s.material.floats._Custom_Data_Offset_Use&&p.CustomDataModule?.enabled){ox+=this.sample(p.CustomDataModule.vector0_0,u);oy+=this.sample(p.CustomDataModule.vector0_1,u);}
   if(uv?.enabled){const nx=uv.tilesX,ny=uv.tilesY,total=nx*ny;const f=Math.floor((((this.sample(uv.startFrame,0)+this.sample(uv.frameOverTime,u)*uv.cycles)%1)+1)%1*total);sx/=nx;sy/=ny;ox+=(f%nx)/nx;oy+=1-(Math.floor(f/nx)+1)/ny;}
   this.map.repeat.set(sx,sy);this.map.offset.set(ox,1-sy-oy);
  }
 }
}
