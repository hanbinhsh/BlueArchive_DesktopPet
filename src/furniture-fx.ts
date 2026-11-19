import * as THREE from 'three';
import {particleShaderData} from './particle-streams';

// Authored DSFX water equations. UVs are converted back to Unity convention
// before source texture transforms, then flipped for embedded PNG sampling.
export async function attachWaterFx(material:THREE.MeshBasicMaterial,parser:any,textures:Set<THREE.Texture>){
 const spec=material.userData.BA_waterFx;if(!spec)return undefined;
 const f=spec.floats,uniforms:Record<string,THREE.IUniform>={fxTime:{value:0},fxTint:{value:new THREE.Vector4(...spec.color as [number,number,number,number])}};
 const white=new THREE.DataTexture(new Uint8Array([255,255,255,255]),1,1);white.needsUpdate=true;textures.add(white);
 for(const name of ['main','mask','distort']){
  const info=spec[`${name}Texture`];
  const texture=info?await parser.getDependency('texture',info.index):white;texture.colorSpace=THREE.NoColorSpace;textures.add(texture);
  uniforms[`${name}Tex`]={value:texture};uniforms[`${name}ST`]={value:new THREE.Vector4(...(info?.st||[1,1,0,0]) as [number,number,number,number])};
 }
 uniforms.fxAtlas={value:new THREE.Vector4(1,1,0,0)};uniforms.cd1={value:new THREE.Vector4()};uniforms.cd2={value:new THREE.Vector4()};
 uniforms.fxSpeeds={value:new THREE.Vector4(f._Mask_Speed_X||0,f._Mask_Speed_Y||0,f._Dis_Speed_X||0,f._Dis_Speed_Y||0)};
 uniforms.fxMainSpeed={value:new THREE.Vector2(f._Main_Speed_X||0,f._Main_Speed_Y||0)};
 uniforms.fxPower={value:new THREE.Vector2(f._Distortion_Power_X||0,f._Distortion_Power_Y||0)};
 uniforms.fxUVAddST={value:new THREE.Vector4(...(spec.uvAddST||[0,0,0,0]) as [number,number,number,number])};
 uniforms.fxParams={value:new THREE.Vector4(f._Step_Power||0,f._Multiply??1,f._RGBRGBA||0,f._Main_Texture_No||0)};
 material.transparent=true;material.depthWrite=material.userData.BA_depthWrite!==false;
 material.blending=THREE.CustomBlending;material.blendEquation=THREE.AddEquation;
 material.blendSrc=spec.kind==='multiply'?THREE.DstColorFactor:THREE.OneFactor;
 material.blendDst=spec.kind==='multiply'?THREE.ZeroFactor:THREE.OneMinusSrcAlphaFactor;
 // Multiplication changes underlying RGB, not the silhouette/desktop alpha.
 material.blendSrcAlpha=spec.kind==='multiply'?THREE.ZeroFactor:THREE.OneFactor;
 material.blendDstAlpha=spec.kind==='multiply'?THREE.OneFactor:THREE.OneMinusSrcAlphaFactor;
 material.onBeforeCompile=shader=>{
  Object.assign(shader.uniforms,uniforms);
  shader.vertexShader='varying vec2 fxUV;\n'+shader.vertexShader.replace('#include <uv_vertex>','#include <uv_vertex>\nfxUV=vec2(uv.x,1.-uv.y);');
  shader.fragmentShader=`varying vec2 fxUV;
uniform float fxTime;uniform vec4 fxAtlas,cd1,cd2;uniform vec4 fxTint,mainST,maskST,distortST,fxSpeeds,fxParams,fxUVAddST;
uniform vec2 fxMainSpeed,fxPower;
uniform sampler2D mainTex,maskTex,distortTex;
vec4 sourceTex(sampler2D tex,vec2 uv){return texture2D(tex,vec2(uv.x,1.-uv.y));}
`+shader.fragmentShader.replace('#include <map_fragment>',spec.kind==='step'?`
vec2 uv=fxUV;
vec2 distortUV=uv*distortST.xy+distortST.zw+fxTime*fxSpeeds.zw;
vec2 distortion=sourceTex(distortTex,distortUV).rg*(fxPower+${f._Custom_Data_Distort_Power_Use?'cd2.xy':'vec2(0.)'});
float uvAdd=${f._UV_Add_Use?'dot(uv*fxUVAddST.xy+fxUVAddST.zw,vec2(1.))':'1.'};
vec2 maskUV=uv*maskST.xy+maskST.zw+fxTime*fxSpeeds.xy+distortion*uvAdd+${f._Custom_Data_Mask_Offset_Usecustom78?'cd2.zw':'vec2(0.)'};
float coverage=step(${f._Step_Scroll_Use?(f._Step_Custom_DataVertex_color_Use?'1.-fxTint.a':'cd1.x'):'fxParams.x'},sourceTex(maskTex,maskUV).r);
vec4 mainSample=sourceTex(mainTex,uv*mainST.xy+mainST.zw+fxTime*fxMainSpeed+distortion*uvAdd+${f._Custom_Data_Main_Offset_Use?'cd1.zw':'vec2(0.)'});
float mainAlpha=mix(mainSample.r,mainSample.a,fxParams.z);
diffuseColor=vec4(mainSample.rgb*coverage*fxTint.rgb*fxParams.y*mainAlpha,clamp(coverage*fxTint.a*mainAlpha*fxParams.y,0.,1.));
`:`
vec4 mainSample=sourceTex(mainTex,fxUV*mainST.xy+mainST.zw);
float mainAlpha=mix(mainSample.r,mainSample.a,fxParams.z);
diffuseColor=vec4(mix(vec3(1.),fxTint.rgb*fxParams.y*mix(mainSample.rgb,vec3(1.),fxParams.w),mainAlpha),1.);
`).replace('#include <premultiplied_alpha_fragment>','');
 };
 // These switches generate GLSL, so different authored switches must not
 // share the first material's compiled program.
 material.customProgramCacheKey=()=>`BA-water-${spec.kind}-${JSON.stringify([f._Custom_Data_Distort_Power_Use,f._UV_Add_Use,f._Custom_Data_Mask_Offset_Usecustom78,f._Step_Scroll_Use,f._Step_Custom_DataVertex_color_Use,f._Custom_Data_Main_Offset_Use])}`;material.needsUpdate=true;
 return (time:number)=>{uniforms.fxTime.value=time;uniforms.fxParams.value.x=f._Step_Power||0;uniforms.fxAtlas.value.fromArray(material.userData.BA_uvFrame||[1,1,0,0]);const data=particleShaderData(material.userData.BA_cafeParticle?.renderer?.m_VertexStreams,material.userData.BA_customData||[[0,0,0,0],[0,0,0,0]]);uniforms.cd1.value.fromArray(data[0]);uniforms.cd2.value.fromArray(data[1]);if(material.userData.BA_cafeParticle){const c=material.color;uniforms.fxTint.value.set(c.r,c.g,c.b,material.opacity);uniforms.fxParams.value.y=1;}};
}
