import * as THREE from 'three';

// Clip a poured stream or floor-occluded body at an authored surface plane.
// The plane follows the animated reference node rather than a fixed world height.
export function attachLiquidReceiver(material:THREE.Material,root:THREE.Object3D){
 const spec=material.userData.BA_liquidReceiver;if(!spec)return undefined;
 const vessel=root.getObjectByName(spec.node);if(!vessel)throw Error('缺少水流接收容器：'+spec.node);
 const gate=spec.gate?root.getObjectByName(spec.gate.node):null;
 if(spec.gate&&!gate)throw Error('缺少裁剪参考节点：'+spec.gate.node);
 const align=spec.gate?.alignNode?root.getObjectByName(spec.gate.alignNode):null;
 if(spec.gate?.alignNode&&!align)throw Error('缺少裁剪对齐节点：'+spec.gate.alignNode);
 const target=spec.gate?.targetNode?root.getObjectByName(spec.gate.targetNode):null;
 if(spec.gate?.targetNode&&!target)throw Error('缺少裁剪目标节点：'+spec.gate.targetNode);
 const plane={value:new THREE.Vector4()},normal=new THREE.Vector3(...spec.normal);
 const local=new THREE.Plane(normal.clone(),spec.constant);
 const gatePos=new THREE.Vector3(),vesselInv=new THREE.Matrix4();
 const alignMat=new THREE.Matrix4(),alignPos=new THREE.Vector3(),alignQuat=new THREE.Quaternion(),alignScale=new THREE.Vector3();
 const upVec=new THREE.Vector3(),targetPos=new THREE.Vector3(),delta=new THREE.Vector3();
 material.userData._BA_clipPlane=plane;
 const previous=material.onBeforeCompile.bind(material),key=material.customProgramCacheKey();
 material.onBeforeCompile=(shader,renderer)=>{
  previous(shader,renderer);shader.uniforms.liquidPlane=plane;
  shader.vertexShader='varying vec3 liquidWorld;\n'+shader.vertexShader.replace('#include <project_vertex>','#include <project_vertex>\nliquidWorld=(modelMatrix*vec4(transformed,1.)).xyz;');
  shader.fragmentShader='uniform vec4 liquidPlane;varying vec3 liquidWorld;\n'+shader.fragmentShader.replace('#include <clipping_planes_fragment>','#include <clipping_planes_fragment>\nif(dot(liquidPlane.xyz,liquidWorld)+liquidPlane.w<0.)discard;');
 };
 material.customProgramCacheKey=()=>key+'-liquid-receiver';material.needsUpdate=true;
 return ()=>{
  vessel.updateWorldMatrix(true,false);
  let constant=spec.constant;
  if(gate&&spec.gate){
   gate.updateWorldMatrix(true,false);
   vesselInv.copy(vessel.matrixWorld).invert();
   gatePos.setFromMatrixPosition(gate.matrixWorld).applyMatrix4(vesselInv);
   const h=gatePos.dot(normal);
   let released=h>=spec.gate.maxHeight;
   if(!released&&align){
    align.updateWorldMatrix(true,false);
    alignMat.multiplyMatrices(vesselInv,align.matrixWorld);
    alignMat.decompose(alignPos,alignQuat,alignScale);
    if(typeof spec.gate.minScale==='number'&&Math.min(Math.abs(alignScale.x),Math.abs(alignScale.y),Math.abs(alignScale.z))<spec.gate.minScale)released=true;
    if(!released&&typeof spec.gate.minUpDot==='number'&&upVec.copy(normal).applyQuaternion(alignQuat).dot(normal)<spec.gate.minUpDot)released=true;
    if(!released&&target&&typeof spec.gate.maxLateral==='number'){
     target.updateWorldMatrix(true,false);
     targetPos.setFromMatrixPosition(target.matrixWorld).applyMatrix4(vesselInv);
     delta.subVectors(alignPos,targetPos);delta.addScaledVector(normal,-delta.dot(normal));
     if(delta.length()>spec.gate.maxLateral)released=true;
    }
   }
   if(released)constant=spec.gate.fallbackConstant;
   else if(typeof spec.gate.followOffset==='number')constant=-(h+spec.gate.followOffset);
  }
  local.set(normal,constant);
  const p=local.clone().applyMatrix4(vessel.matrixWorld);
  plane.value.set(p.normal.x,p.normal.y,p.normal.z,p.constant);
 };
}
