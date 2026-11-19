import * as THREE from 'three';

// Clip a poured stream at the receiving vessel's inner surface. The plane
// follows the animated vessel, rather than a fixed world height.
export function attachLiquidReceiver(material:THREE.Material,root:THREE.Object3D){
 const spec=material.userData.BA_liquidReceiver;if(!spec)return undefined;
 const vessel=root.getObjectByName(spec.node);if(!vessel)throw Error('缺少水流接收容器：'+spec.node);
 const plane={value:new THREE.Vector4()},local=new THREE.Plane(new THREE.Vector3(...spec.normal),spec.constant);
 const previous=material.onBeforeCompile.bind(material),key=material.customProgramCacheKey();
 material.onBeforeCompile=(shader,renderer)=>{
  previous(shader,renderer);shader.uniforms.liquidPlane=plane;
  shader.vertexShader='varying vec3 liquidWorld;\n'+shader.vertexShader.replace('#include <project_vertex>','#include <project_vertex>\nliquidWorld=(modelMatrix*vec4(transformed,1.)).xyz;');
  shader.fragmentShader='uniform vec4 liquidPlane;varying vec3 liquidWorld;\n'+shader.fragmentShader.replace('#include <clipping_planes_fragment>','#include <clipping_planes_fragment>\nif(dot(liquidPlane.xyz,liquidWorld)+liquidPlane.w<0.)discard;');
 };
 material.customProgramCacheKey=()=>key+'-liquid-receiver';material.needsUpdate=true;
 return ()=>{vessel.updateWorldMatrix(true,false);const p=local.clone().applyMatrix4(vessel.matrixWorld);plane.value.set(p.normal.x,p.normal.y,p.normal.z,p.constant);};
}
