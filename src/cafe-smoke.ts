import * as THREE from 'three';
import {particleShaderData} from './particle-streams';
import {cafeMaterialShaders} from './cafe-material-shaders';

export interface CafeDepth {
 texture:THREE.IUniform;size:THREE.IUniform;range:THREE.IUniform;scale:THREE.IUniform;
 required:boolean;
}

// Equations transcribed from the original D3D programs, not from the texture
// names. Cloud RGB channels encode shading/coverage, rather than visible RGB.
const cloud=`
vec2 db=fxUV*distortST.xy+distortST.zw;
vec2 mb=fxUV*mainST.xy+mainST.zw;
vec2 du=pair(cd1*_CustomData_DistortTiling_CD1XYXY*db.xyxy)+pair(cd2*_CustomData_DistortTiling_CD2XYXY*db.xyxy)
       +pair(cd1*_CustomData_DistortOffset_CD1XYXY)+pair(cd2*_CustomData_DistortOffset_CD2XYXY);
vec2 mu=pair(cd1*_CustomData_MainTiling_CD1XYXY*mb.xyxy)+pair(cd2*_CustomData_MainTiling_CD2XYXY*mb.xyxy)
       +pair(cd1*_CustomData_MainOffset_CD1XYXY)+pair(cd2*_CustomData_MainOffset_CD2XYXY);
vec2 distort=sourceTex(distortTex,db+fract(fxTime*vec2(_Dis_Speed_X,_Dis_Speed_Y))+du).rg;
vec2 uvMain=mb+fxTime*vec2(_Main_Speed_X,_Main_Speed_Y)+mu
       +distort*(vec2(_Distortion_Power_X,_Distortion_Power_Y)+pair(cd2*_CustomData_DistortPower_CD2XYXY));
vec4 sampleMain=sourceTex(mainTex,uvMain);
vec2 steps=pair(cd1*_CustomData_StepValue_CD1XYXY)+vec2(_GStep_Value,_BStep_Value);
float alpha=clamp((sampleMain.b-steps.y)*_BStep_Glow_Value,0.,1.)*sampleMain.a*_RColor.a*_Mutiply*particleColor.a;
float sceneDepth=mix(fxDepthRange.x,fxDepthRange.y,texture2D(fxDepthTex,gl_FragCoord.xy/fxDepthSize).r);
float distanceToOpaque=(sceneDepth-fxEyeDepth)/max(fxUnitScale,.00001);
alpha*=clamp((distanceToOpaque-_SoftParticleNearFade)/max(.00001,_SoftParticleFarFade-_SoftParticleNearFade),0.,1.);
vec2 power=pair(cd1*_CustomData_ShadingPower_CD1_GColorShadowXYXY);
float shadowSample=sourceTex(mainTex,uvMain+pair(cd2*_CustomData_ShadingOffset_CD2_ShadowOffsetXYXY)+vec2(_Shadow_Offset_X,_Shadow_Offset_Y)).b;
float shadow=clamp((steps.y-shadowSample-_Shadow_Power-power.y)*_Shadow_Glow_Value,0.,1.);
vec3 base=mix(sampleMain.r,_Shadow_Color_Multiply,shadow)*particleColor.rgb;
float highlightSample=sourceTex(mainTex,uvMain+pair(cd2*_CustomData_ShadingOffset_CD2_GColorOffsetXYXY)+vec2(_GColor_Offset_X,_GColor_Offset_Y)).b;
float highlight=min(1.,clamp((sampleMain.g-steps.x)*_GColor_Glow_Value,0.,1.)+clamp((steps.y-highlightSample-_GColor_Power-power.x)*_GColor_Glow_Value,0.,1.));
vec3 rgb=mix(base,_GColor.rgb,highlight)*_Mutiply*_RColor.rgb;
diffuseColor=vec4(rgb*alpha,clamp(alpha,0.,1.));
if(diffuseColor.a<_Alphaclip_Value)discard;
`;

const smooth=`
vec2 dissolveUV=fxUV*_GTillingxyOffsetzw.xy+_GTillingxyOffsetzw.zw+fxTime*vec2(_GDissolve_Speed_X,_GDissolve_Speed_Y)+cd2.zw;
float dissolve=sourceTex(dissolveTex,dissolveUV).g*_GDissolve_Str;
float gra=mix(dissolve,fxUV.x*_Gra_TillingxyOffsetzw.x+_Gra_TillingxyOffsetzw.z,_Gra_Lerp);
float value=clamp((gra-_Subtract-cd1.x)/max(.00001,_Smooth+cd1.y),0.,1.);
float coverage=value*value*(3.-2.*value);
vec4 sampleMain=sourceTex(mainTex,fxUV*mainST.xy+mainST.zw+fxTime*vec2(_Main_Speed_X,_Main_Speed_Y)+cd1.zw);
float mask=sourceTex(maskTex,fxUV*maskST.xy+maskST.zw+fxTime*vec2(_Mask_Speed_X,_Mask_Speed_Y)+cd2.xy).g;
float alpha=coverage*mix(sampleMain.r,sampleMain.a,_RGBA)*particleColor.a*_Alpha*sampleMain.a*_Color.a*mask;
diffuseColor=vec4(sampleMain.rgb*particleColor.rgb*_Color.rgb,clamp(alpha,0.,1.));
if(diffuseColor.a<_Alphaclip_Value)discard;
`;

const puff=`
float threshold=_BCustom_Data_Use!=0.?(_Step_Custom_DataVertex_color_Use!=0.?1.-particleColor.a:cd1.w):_BDisappear_Offset;
vec2 uvMain=fxUV*mainST.xy+mainST.zw+fxTime*vec2(_Main_Speed_X,_Main_Speed_Y);
if(_Custom_Data_Main_Offset_Use!=0.)uvMain+=cd1.xy;
vec4 sampleMain=sourceTex(mainTex,uvMain);
float alpha=clamp((sampleMain.b-threshold)*_BStep_Glow_Value,0.,1.)*sampleMain.a*_RColor.a*_Mutiply;
float shadow=clamp((threshold-sampleMain.b-_Shadow_Value)*_Shadow_Glow_Value,0.,1.);
vec3 base=mix(sampleMain.r,_Shadow_Color_Multiply,shadow)*particleColor.rgb*_RColor.rgb;
vec3 highlight=_Color_Custom_Data_Use!=0.?cd2.rgb:_GColor.rgb;
float amount=clamp((sampleMain.g-(_GCustom_Data_Use!=0.?cd1.z:_GDisappear_Offset))*_GColor_Glow_Value,0.,1.);
diffuseColor=vec4(mix(base,highlight,amount)*_Mutiply,clamp(alpha*(_Vertex_Alpha_Use!=0.?1.:particleColor.a),0.,1.));
`;

const pixel=`
float threshold=_BCustom_Data_Use!=0.?cd1.w:_BDisappear_Offset;
vec2 offset=_Custom_Data_MainMask_Offset_Use!=0.?cd1.xy:fxTime*vec2(_Main_Speed_X,_Main_Speed_Y);
vec4 sampleMain=sourceTex(mainTex,fxUV*mainST.xy+mainST.zw+offset);
float alpha=(sampleMain.b>threshold?1.:0.)*sampleMain.a*particleColor.a*_MainColor.a*_Multiply;
float shadow=sampleMain.b+_Shadow_Value<threshold?1.:0.;
vec3 base=mix(sampleMain.r,_Shadow_Color_Multiply,shadow)*particleColor.rgb*_MainColor.rgb;
vec3 highlight=_Color_Custom_Data_Use!=0.?cd2.rgb:_GColor.rgb;
float amount=clamp((sampleMain.g-(_GCustom_Data_Use!=0.?cd1.z:_GDisappear_Offset))*_GColor_Sharpness,0.,1.);
diffuseColor=vec4(mix(base,highlight,amount)*_Multiply,clamp(alpha,0.,1.));
`;

cafeMaterialShaders.cloudNoDepth=cloud.replace(/float sceneDepth=[\s\S]*?alpha\*=.*?;/,'');

export async function attachCafeSmoke(material:THREE.MeshBasicMaterial,parser:any,textures:Set<THREE.Texture>,depth:CafeDepth){
 const spec=material.userData.BA_smokeFx;if(!spec)return undefined;
 const uniforms:Record<string,THREE.IUniform>={fxTime:{value:0},fxAtlas:{value:new THREE.Vector4(1,1,0,0)},cd1:{value:new THREE.Vector4()},cd2:{value:new THREE.Vector4()},fxDepthTex:depth.texture,fxDepthSize:depth.size,fxDepthRange:depth.range,fxUnitScale:depth.scale};
 const declarations:string[]=[];
 const streams=material.userData.BA_cafeParticle?.renderer?.m_VertexStreams;
 // Stream packing is evaluated per material on the CPU; all layouts use
 // the same shader registers, including a Custom2-only source layout.
 for(const [name,value] of Object.entries(spec.floats)){if(!/^_[A-Za-z0-9_]+$/.test(name))continue;uniforms[name]={value};declarations.push(`uniform float ${name};`);}
 for(const [name,value] of Object.entries(spec.colors)){if(!/^_[A-Za-z0-9_]+$/.test(name))continue;uniforms[name]={value:new THREE.Vector4(...value as [number,number,number,number])};declarations.push(`uniform vec4 ${name};`);}
 const white=new THREE.DataTexture(new Uint8Array([255,255,255,255]),1,1);white.needsUpdate=true;textures.add(white);
 for(const name of ['main','mask','distort','dissolve']){
  const info=spec[`${name}Texture`];let texture=white;
  if(info){texture=await parser.getDependency('texture',info.index);texture.colorSpace=THREE.NoColorSpace;textures.add(texture);}
  uniforms[`${name}Tex`]={value:texture};uniforms[`${name}ST`]={value:new THREE.Vector4(...(info?.st||[1,1,0,0]) as [number,number,number,number])};
 }
 material.blending=THREE.CustomBlending;material.blendSrc=['cloud','blend','mask','distort','distortSoft','step','add'].includes(spec.kind)?THREE.OneFactor:THREE.SrcAlphaFactor;material.blendDst=THREE.OneMinusSrcAlphaFactor;
 if(['channel','classic','distort1','step1','doubleSoft','doubleDistort','cloudNoDepth'].includes(spec.kind)){material.blendSrc=spec.floats._SrcBlend===1?THREE.OneFactor:THREE.SrcAlphaFactor;material.blendDst=spec.floats._DstBlend===1?THREE.OneFactor:THREE.OneMinusSrcAlphaFactor;}
 if(spec.kind==='add')material.blendDst=THREE.OneFactor;
 if(spec.kind==='multiply'){material.blendSrc=THREE.DstColorFactor;material.blendDst=THREE.ZeroFactor;}
 if(['unlit','unlitVC'].includes(spec.kind)){material.blendSrc=THREE.OneFactor;material.blendDst=THREE.ZeroFactor;}
 if(spec.kind==='matcap'){material.blendSrc=THREE.OneFactor;material.blendDst=THREE.ZeroFactor;}
 material.blendSrcAlpha=THREE.OneFactor;material.blendDstAlpha=THREE.OneMinusSrcAlphaFactor;
 if(spec.kind==='multiply'){material.blendSrcAlpha=THREE.ZeroFactor;material.blendDstAlpha=THREE.OneFactor;}
 material.depthWrite=false;
 if(['unlit','unlitVC'].includes(spec.kind))material.depthWrite=material.userData.BA_depthWrite===true;
 if(spec.kind==='matcap')material.depthWrite=material.userData.BA_depthWrite===true;
 if(['cloud','doubleSoft','distortSoft'].includes(spec.kind))depth.required=true;
 material.onBeforeCompile=shader=>{
  Object.assign(shader.uniforms,uniforms);
  shader.vertexShader=(spec.kind==='channel'?'attribute vec2 fxSecondUV;':'')+'varying vec2 fxUV2;varying vec2 fxUV;varying float fxEyeDepth;\n'+shader.vertexShader.replace('#include <uv_vertex>','#include <uv_vertex>\nfxUV=vec2(uv.x,1.-uv.y);fxUV2='+ (spec.kind==='channel'?'vec2(fxSecondUV.x,1.-fxSecondUV.y);':'fxUV;')).replace('#include <project_vertex>','#include <project_vertex>\nfxEyeDepth=-mvPosition.z;');
  if(spec.kind==='matcap')shader.vertexShader='varying vec3 fxViewNormal;\n'+shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nfxViewNormal=normalize(normalMatrix*normal);');
  shader.fragmentShader=`varying vec2 fxUV2;varying vec2 fxUV;varying float fxEyeDepth;
uniform float fxTime,fxUnitScale;uniform vec4 fxAtlas,cd1,cd2,mainST,maskST,distortST,dissolveST;
uniform vec2 fxDepthSize,fxDepthRange;uniform sampler2D fxDepthTex,mainTex,maskTex,distortTex,dissolveTex;
vec2 pair(vec4 v){return v.xy+v.zw;}
vec4 sourceTex(sampler2D tex,vec2 uv){return texture2D(tex,vec2(uv.x,1.-uv.y));}
${declarations.join('\n')}
`+shader.fragmentShader.replace('#include <map_fragment>',`vec2 animatedUV=fxUV*fxAtlas.xy+fxAtlas.zw;vec4 particleColor=diffuseColor;
vec4 shaderData1=cd1,shaderData2=cd2;
#if defined(USE_COLOR_ALPHA)
particleColor*=vColor;
#elif defined(USE_COLOR)
particleColor.rgb*=vColor;
#endif
${(cafeMaterialShaders[spec.kind]||(spec.kind==='cloud'?cloud:spec.kind==='puff'?puff:spec.kind==='pixel'?pixel:smooth)).replace(/\bfxUV\b/g,'animatedUV').replace(/\bcd1\b/g,'shaderData1').replace(/\bcd2\b/g,'shaderData2')}
${['blend','channel'].includes(spec.kind)?'diffuseColor.rgb*=particleColor.a;':['mask','distort','distortSoft'].includes(spec.kind)?'diffuseColor.rgb*=particleColor.a*particleColor.a;':spec.kind==='step'?'diffuseColor.rgb*=(_Vertex_Alpha_Use!=0.?1.:particleColor.a);':''}
${spec.kind==='add'?'diffuseColor.a=clamp(max(max(diffuseColor.r,diffuseColor.g),diffuseColor.b),0.,1.);':''}`).replace('#include <color_fragment>','').replace('#include <premultiplied_alpha_fragment>','');
  if(spec.kind==='matcap')shader.fragmentShader='varying vec3 fxViewNormal;\n'+shader.fragmentShader;
  if(material.blendSrc===THREE.OneFactor&&material.blendDst===THREE.OneMinusSrcAlphaFactor)shader.fragmentShader=shader.fragmentShader.replace('#include <colorspace_fragment>','gl_FragColor.rgb/=max(gl_FragColor.a,1e-7);\n#include <colorspace_fragment>\ngl_FragColor.rgb*=gl_FragColor.a;');
 };
 material.customProgramCacheKey=()=>`BA-smoke-${spec.kind}-${declarations.join('|')}-${material.blendSrc}-${material.blendDst}`;material.needsUpdate=true;
 return (time:number)=>{uniforms.fxTime.value=time;for(const tr of material.userData.BA_cafeParticle?.propertyTracks||[]){const u=uniforms[tr.property];if(u){if(tr.category==='floats')u.value=spec.floats[tr.property];else u.value.fromArray(spec.colors[tr.property]);}}uniforms.fxAtlas.value.fromArray(material.userData.BA_uvFrame||[1,1,0,0]);const raw=material.userData.BA_customData||[[0,0,0,0],[0,0,0,0]],data=['step','twoStep'].includes(spec.kind)?particleShaderData(streams,raw):raw;uniforms.cd1.value.fromArray(data[0]);uniforms.cd2.value.fromArray(data[1]);};
}
