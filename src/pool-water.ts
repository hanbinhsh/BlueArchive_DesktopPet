import * as THREE from 'three';
// MX/Water's authored foam mask and dual wave samples. Equations/transforms
// match its shipped vertex/fragment programs; it has no depth-fade term.
export async function attachPoolWater(material:THREE.MeshBasicMaterial,parser:any,textures:Set<THREE.Texture>){
 const s=material.userData.BA_poolWater;if(!s)return;
 const u:Record<string,THREE.IUniform>={poolTime:{value:0}};
 for(const key of ['_FoamMaskTex','_FoamTex','_WaveTex']){const original=await parser.getDependency('texture',s[key].index);const t=original.clone();t.colorSpace=s[key].srgb?THREE.SRGBColorSpace:THREE.NoColorSpace;t.needsUpdate=true;textures.add(t);u[key]={value:t};u[key+'_ST']={value:new THREE.Vector4(...s[key].st as [number,number,number,number])};}
 for(const key of ['_BaseColor','_FoamColor','_WaveColor','_DeepWaveColor','_MasterColor'])u[key]={value:new THREE.Vector4(...s.colors[key] as [number,number,number,number])};
 for(const key of ['_FoamValue','_WaveInt','_FoamSpeed','_WaveSpeed_A','_WaveSpeed_B'])u[key]={value:s.floats[key]};
 material.transparent=true;material.depthWrite=true;material.blending=THREE.CustomBlending;material.blendSrc=THREE.SrcAlphaFactor;material.blendDst=THREE.OneMinusSrcAlphaFactor;material.blendSrcAlpha=THREE.OneFactor;material.blendDstAlpha=THREE.OneMinusSrcAlphaFactor;
 material.onBeforeCompile=shader=>{
  Object.assign(shader.uniforms,u);
  shader.vertexShader='varying vec2 poolUV;\n'+shader.vertexShader.replace('#include <uv_vertex>','#include <uv_vertex>\npoolUV=vec2(uv.x,1.-uv.y);');
  shader.fragmentShader=`varying vec2 poolUV;
uniform float poolTime,_FoamValue,_WaveInt,_FoamSpeed,_WaveSpeed_A,_WaveSpeed_B;
uniform sampler2D _FoamMaskTex,_FoamTex,_WaveTex;
uniform vec4 _FoamMaskTex_ST,_FoamTex_ST,_WaveTex_ST,_BaseColor,_FoamColor,_WaveColor,_DeepWaveColor,_MasterColor;
vec4 poolSample(sampler2D t,vec2 p){return texture2D(t,vec2(p.x,1.-p.y));}
vec2 poolST(vec2 p,vec4 st){return p*st.xy+st.zw;}
`+shader.fragmentShader.replace('#include <map_fragment>',`
float t=poolTime*.1;
vec2 foamA=poolST(poolUV+vec2(t*_FoamSpeed,-t*_FoamSpeed),_FoamTex_ST);
vec2 foamB=poolST(poolUV+vec2(-t*_FoamSpeed,t*_FoamSpeed),_FoamTex_ST);
vec2 waveA=poolST(poolUV+vec2(t*_WaveSpeed_A,t*_WaveSpeed_B),_WaveTex_ST);
vec2 waveB=poolST(poolUV+vec2(-t*_WaveSpeed_A,-t*_WaveSpeed_B),_WaveTex_ST);
float distortion=poolSample(_WaveTex,waveA).b*_WaveInt*.1;
vec4 wa=poolSample(_WaveTex,waveA+distortion),wb=poolSample(_WaveTex,waveB+distortion);
float wave=wa.r*wb.g;wave*=step(.2,wave);
vec3 deep=wb.g*_DeepWaveColor.rgb;deep*=step(vec3(.1),deep);
float mask=poolSample(_FoamMaskTex,poolST(poolUV,_FoamMaskTex_ST)).r;
float foam=poolSample(_FoamTex,foamA).r*poolSample(_FoamTex,foamB).g*pow(mask,_FoamValue*.6)+pow(mask,_FoamValue);foam*=step(.2,foam);
diffuseColor=(clamp(_BaseColor+foam*_FoamColor,0.,1.)+wave*_WaveColor+vec4(deep,0.))*_MasterColor;
`);
 };
 material.customProgramCacheKey=()=> 'BA-MX-Water-035';material.needsUpdate=true;return(time:number)=>{u.poolTime.value=time;};
}
