// Original DSFX fragment equations, checked against the bundled D3D programs.
// Texture/color channels are data: sampling the image as ordinary RGB loses
// masks, dissolves and premultiplied blend behavior.
export const cafeMaterialShaders:Record<string,string>={
 smokeDistortion:`
vec2 offset=_Custom_Data_MainMask_Offset_Use!=0.?cd1.xy:fxTime*vec2(_Main_Speed_X,_Main_Speed_Y);
vec2 distortion=sourceTex(distortTex,fxUV*distortST.xy+distortST.zw+fxTime*vec2(_Dis_Speed_X,_Dis_Speed_Y)+vec2(0.,1.)).rg*vec2(_Distortion_Power_X,_Distortion_Power_Y);
vec4 tex=sourceTex(mainTex,fxUV*mainST.xy+mainST.zw+offset+distortion);
float threshold=_BCustom_Data_Use!=0.?cd1.w:_BDisappear_Offset;
float shadow=tex.b+_Shadow_Value<threshold?1.:0.;
vec3 base=mix(tex.r,_Shadow_Color_Multiply,shadow)*particleColor.rgb*_MainColor.rgb;
float highlight=clamp((tex.g-(_GCustom_Data_Use!=0.?cd1.z:_GDisappear_Offset))*_GColor_Sharpness,0.,1.);
float alpha=tex.b>threshold?tex.a*particleColor.a*_Mutiply*_MainColor.a:0.;
diffuseColor=vec4(mix(base,_Color_Custom_Data_Use!=0.?cd2.rgb:_GColor.rgb,highlight)*_Mutiply,clamp(alpha,0.,1.));`,
 flowmap:`
vec2 flow=(sourceTex(distortTex,fxUV*distortST.xy+distortST.zw).rg*2.-1.)*(_Flowspeed_Data_Use!=0.?cd1.y:_FlowSpeed);
float phaseA=fract(fxTime*.5),phaseB=fract(fxTime*.5+.5);
vec4 sampleMain=mix(sourceTex(mainTex,fxUV-flow*phaseB),sourceTex(mainTex,fxUV-flow*phaseA),abs(1.-2.*phaseB));
float threshold=_BCustom_Data_Use!=0.?cd1.w:_BDisappear_Offset;
float shadow=clamp((threshold-sampleMain.b-(_Shadow_Value_Data_Use!=0.?cd1.x:_Shadow_Value))*_Shadow_Glow_Value,0.,1.);
vec3 base=mix(sampleMain.r,_Shadow_Color_Multiply,shadow)*particleColor.rgb*_RColor.rgb;
float highlight=clamp((sampleMain.g-(_GCustom_Data_Use!=0.?cd1.z:_GDisappear_Offset))*_GColor_Sharpness,0.,1.);
vec3 rgb=mix(base,_Color_Custom_Data_Use!=0.?cd2.rgb:_GColor.rgb,highlight)*_Mutiply;
float alpha=clamp((sampleMain.b-threshold)*_BStep_Glow_Value,0.,1.)*sampleMain.a*particleColor.a*_RColor.a*_Mutiply;
diffuseColor=vec4(rgb,clamp(alpha,0.,1.));`,
 stepTwoSide:`
float mask=sourceTex(maskTex,fxUV*maskST.xy+maskST.zw+fxTime*vec2(_Mask_Speed_X,_Mask_Speed_Y)+(_Custom_Data_Mask_Offset_Use!=0.?cd1.xy:vec2(0.))).r;
float coverage=step(_Custom_Data_Use!=0.?cd1.z:_Step_Power,mask);
vec4 tex=sourceTex(mainTex,fxUV*mainST.xy+mainST.zw+fxTime*vec2(_Main_Speed_X,_Main_Speed_Y)+(_Custom_Data_Main_Offset_Use!=0.?cd1.xy:vec2(0.)));
float alpha=clamp((_RGBRGBA!=0.?tex.a:tex.r)*coverage*particleColor.a*_Multiply,0.,1.);
if(alpha<_AlphaClip_Value)discard;
vec3 front=tex.rgb*_FrontFacesColor.rgb*particleColor.rgb,back=tex.rgb*_BackFacesColor.rgb*cd2.rgb;
diffuseColor=vec4(mix(back,front,gl_FrontFacing?1.:.5)*coverage*_Multiply,alpha);`,
 blend:`
vec2 uvMain=fxUV*mainST.xy+mainST.zw+(_Custom_Data_Offset_Use!=0.?cd1.xy:vec2(0.));
vec4 tex=sourceTex(mainTex,uvMain);float alpha=_RGBRGBA!=0.?tex.a:tex.r;
diffuseColor=vec4((_Main_Texture_No!=0.?vec3(1.):tex.rgb)*particleColor.rgb*_Color.rgb*_Multiply*alpha,clamp(alpha*particleColor.a*_Color.a*_Multiply,0.,1.));`,
 mask:`
vec4 offsets=_Custom_Data_MainMask_Offset_Use!=0.?cd1:vec4(0.);
vec4 tex=sourceTex(mainTex,fxUV*mainST.xy+mainST.zw+fxTime*vec2(_Main_Speed_X,_Main_Speed_Y)+offsets.xy);
float mask=sourceTex(maskTex,fxUV*maskST.xy+maskST.zw+fxTime*vec2(_Mask_Speed_X,_Mask_Speed_Y)+offsets.zw).r;
vec3 alpha=_RGBRGBA!=0.?vec3(tex.a):tex.rgb;
diffuseColor=vec4(tex.rgb*particleColor.rgb*_Color.rgb*alpha*mask*_Multiply,clamp(alpha.r*particleColor.a*particleColor.a*_Color.a*mask*_Multiply,0.,1.));`,
 distort:`
vec2 distortion=sourceTex(distortTex,fxUV*distortST.xy+distortST.zw+fxTime*vec2(_Dis_Speed_X,_Dis_Speed_Y)).rg;
distortion*=vec2(_Distortion_Power_X,_Distortion_Power_Y)+(_Custom_Data_Distort_Power_Use!=0.?cd2.xy:vec2(0.));
vec4 offsets=_Custom_Data_MainMask_Offset_Use!=0.?cd1:vec4(0.);
vec4 tex=sourceTex(mainTex,fxUV*mainST.xy+mainST.zw+fxTime*vec2(_Main_Speed_X,_Main_Speed_Y)+offsets.xy+(_Main_Distortion_Use!=0.?distortion:vec2(0.)));
float mask=sourceTex(maskTex,fxUV*maskST.xy+maskST.zw+fxTime*vec2(_Mask_Speed_X,_Mask_Speed_Y)+offsets.zw+(_Mask_Distortion_Use!=0.?distortion:vec2(0.))).r;
float alpha=_RGBRGBA!=0.?tex.a:tex.r;
diffuseColor=vec4(tex.rgb*particleColor.rgb*_Color.rgb*mask*_Multiply*tex.a,clamp(alpha*particleColor.a*particleColor.a*_Color.a*mask*_Multiply,0.,1.));`,
 step:`
float mask=sourceTex(maskTex,fxUV*maskST.xy+maskST.zw+fxTime*vec2(_Mask_Speed_X,_Mask_Speed_Y)+(_Custom_Data_Mask_Offset_Use!=0.?cd2.xy:vec2(0.))).r;
float threshold=_Step_Scroll_Use!=0.?(_Step_Custom_DataVertex_color_Use!=0.?1.-particleColor.a:cd1.x):_Step_Power;
float coverage=step(threshold,mask);
vec4 tex=sourceTex(mainTex,fxUV*mainST.xy+mainST.zw+fxTime*vec2(_Main_Speed_X,_Main_Speed_Y)+(_Custom_Data_Main_Offset_Use!=0.?cd1.zw:vec2(0.)));
float alpha=_RGBRGBA!=0.?tex.a:tex.r;
diffuseColor=vec4(tex.rgb*particleColor.rgb*coverage*_Color.rgb*_Multiply*alpha,clamp(coverage*_Color.a*alpha*(_Vertex_Alpha_Use!=0.?1.:particleColor.a)*_Multiply,0.,1.));`,
 multiply:`
vec4 tex=sourceTex(mainTex,fxUV*mainST.xy+mainST.zw+(_Custom_Data_MainMask_Offset_Use!=0.?cd1.xy:vec2(0.)));
float alpha=(_RGBRGBA!=0.?tex.a:tex.r)*particleColor.a;
diffuseColor=vec4(mix(vec3(1.),_Color.rgb*_Multiply*particleColor.rgb*(_Main_Texture_No!=0.?vec3(1.):tex.rgb),alpha),1.);`,
 add:`
vec4 tex=sourceTex(mainTex,fxUV*mainST.xy+mainST.zw+(_Custom_Data_Offset_Use!=0.?cd1.xy:vec2(0.)));
diffuseColor=vec4(tex.rgb*particleColor.rgb*_Color.rgb*particleColor.a*tex.a,1.);`,
 channel:`
vec2 uvR=_RDistort_UV_Channel!=0.?fxUV2:fxUV,uvG=_GDistort_UV_Channel!=0.?fxUV2:fxUV;
vec2 db=fxUV*distortST.xy+distortST.zw;
vec2 ro=pair(cd1*_CustomData_DistortTilingR_CD1XYXY*db.xyxy)+pair(cd2*_CustomData_DistortTilingR_CD2XYXY*db.xyxy)+pair(cd1*_CustomData_DistortOffsetR_CD1XYXY)+pair(cd2*_CustomData_DistortOffsetR_CD2XYXY);
vec2 go=pair(cd1*_CustomData_DistortTilingG_CD1XYXY*db.xyxy)+pair(cd2*_CustomData_DistortTilingG_CD2XYXY*db.xyxy)+pair(cd1*_CustomData_DistortOffsetG_CD1XYXY)+pair(cd2*_CustomData_DistortOffsetG_CD2XYXY);
vec2 dr=sourceTex(distortTex,uvR*_R_Tilingxy_Offsetzw.xy+_R_Tilingxy_Offsetzw.zw+fract(fxTime*vec2(_RDistort_Speed_X,_RDistort_Speed_Y))+ro).rr*(vec2(_RDistort_Power_X,_RDistort_Power_Y)+pair(cd2*_CustomData_DistortPowerR_CD2XYXY));
vec2 dg=sourceTex(distortTex,uvG*_G_Tilingxy_Offsetzw.xy+_G_Tilingxy_Offsetzw.zw+fract(fxTime*vec2(_GDistort_Speed_X,_GDistort_Speed_Y))+go).gg*(vec2(_GDistort_Power_X,_GDistort_Power_Y)+pair(cd2*_CustomData_DistortPowerG_CD2XYXY));
vec2 mb=(_Main_UV_Channel!=0.?fxUV2:fxUV)*mainST.xy+mainST.zw,kb=(_Mask_UV_Channel!=0.?fxUV2:fxUV)*maskST.xy+maskST.zw;
vec2 mo=pair(cd1*_CustomData_MainTiling_CD1XYXY*mb.xyxy)+pair(cd2*_CustomData_MainTiling_CD2XYXY*mb.xyxy)+pair(cd1*_CustomData_MainOffset_CD1XYXY)+pair(cd2*_CustomData_MainOffset_CD2XYXY);
vec2 ko=pair(cd1*_CustomData_MaskTiling_CD1XYXY*kb.xyxy)+pair(cd2*_CustomData_MaskTiling_CD2XYXY*kb.xyxy)+pair(cd1*_CustomData_MaskOffset_CD1XYXY)+pair(cd2*_CustomData_MaskOffset_CD2XYXY);
vec4 tex=sourceTex(mainTex,mb+mo+fxTime*vec2(_Main_Speed_X,_Main_Speed_Y)+(_Tex_Main_Distort==1.?dr:_Tex_Main_Distort==2.?dg:_Tex_Main_Distort==3.?dr+dg:vec2(0.)));
vec3 mask=clamp(sourceTex(maskTex,kb+ko+fxTime*vec2(_Add_Speed_X,_Add_Speed_Y)+(_Tex_Mask_Distort==1.?dr:_Tex_Mask_Distort==2.?dg:vec2(0.))).rgb,0.,1.);
vec2 thresholds=pair(cd1*_CustomData_StepValue_CD1_GStepBStepXYXY);
vec3 stepMask=_Step_Tex_Channel==0.?mask:_Step_Tex_Channel==1.?mask.rrr:_Step_Tex_Channel==2.?mask.ggg:_Step_Tex_Channel==3.?mask.bbb:vec3(1.);
vec3 addMask=_Add_Tex_Channel==0.?mask:_Add_Tex_Channel==1.?mask.rrr:_Add_Tex_Channel==2.?mask.ggg:mask.bbb;
stepMask=clamp((stepMask-thresholds.y-_Step_Tex_Dithering)*_Step_Tex_Multiply,0.,1.);
addMask=clamp((addMask-thresholds.x-_Add_Tex_Dithering)*_Add_Tex_Multiply,0.,1.);addMask=clamp(addMask*(_Main_Tex_Alpha_use!=0.?tex.a:1.),0.,1.);
vec3 alpha=_RGBRGBA!=0.?vec3(tex.a):tex.rgb;
vec3 base=tex.rgb*particleColor.rgb*_Main_Color.rgb*_Main_Multiply*tex.a*alpha;
diffuseColor=vec4(mix(base*stepMask,_Add_Color.rgb,addMask),stepMask.r*clamp(alpha.r*particleColor.a*_Main_Color.a*_Main_Multiply,0.,1.));`
};

// Older water-channel variant: these source materials use no custom offset
// switches. Keep its squared vertex-alpha output from the original PS.
cafeMaterialShaders.classic=`
vec2 ru=fxUV*_R_Tilingxy_Offsetzw.xy+_R_Tilingxy_Offsetzw.zw+fxTime*vec2(_RDistort_Speed_X,_RDistort_Speed_Y);
vec2 gu=fxUV*_G_Tilingxy_Offsetzw.xy+_G_Tilingxy_Offsetzw.zw+fxTime*vec2(_GDistort_Speed_X,_GDistort_Speed_Y);
vec2 rd=sourceTex(distortTex,ru).rr*vec2(_RDistort_Power_X,_RDistort_Power_Y);
vec2 gd=sourceTex(distortTex,gu).gg*vec2(_GDistort_Power_X,_GDistort_Power_Y);
vec2 mo=_Custom_Data_Main_OffsetUse!=0.?cd2.xy:vec2(0.);
vec2 ko=_Custom_Data_Mask_OffsetUse!=0.?cd2.zw:vec2(0.);
vec2 du=_Tex_Main_Distort==1.?rd:_Tex_Main_Distort==2.?gd:vec2(0.);
vec2 ku=_Tex_Mask_Distort==1.?rd:_Tex_Mask_Distort==2.?gd:vec2(0.);
vec4 tex=sourceTex(mainTex,fxUV*mainST.xy+mainST.zw+mo+du+fxTime*vec2(_Main_Speed_X,_Main_Speed_Y));
vec3 mask=clamp(sourceTex(maskTex,fxUV*maskST.xy+maskST.zw+ko+ku+fxTime*vec2(_Add_Speed_X,_Add_Speed_Y)).rgb,0.,1.);
vec3 sm=_Step_Tex_Channel==4.?vec3(1.):_Step_Tex_Channel==1.?mask.rrr:_Step_Tex_Channel==2.?mask.ggg:_Step_Tex_Channel==3.?mask.bbb:mask;
float st=_Custom_Data_Step_Tex_Dithering_use!=0.?cd1.y:_Step_Tex_Dithering;
sm=clamp((sm-st)*_Step_Tex_Multiply,0.,1.);
vec3 am=_Add_Tex_Channel==1.?mask.rrr:_Add_Tex_Channel==2.?mask.ggg:_Add_Tex_Channel==3.?mask.bbb:mask;
float at=_Custom_Data_Add_Tex_Dithering_use!=0.?cd1.x:_Add_Tex_Dithering;
am=clamp((am-at)*_Add_Tex_Multiply,0.,1.)*(_Main_Tex_Alpha_use!=0.?tex.a:1.);
vec3 ac=_RGBRGBA!=0.?vec3(tex.a):tex.rgb;
vec3 base=tex.rgb*particleColor.rgb*_Main_Color.rgb*_Main_Multiply*tex.a*ac;
diffuseColor=vec4(mix(base*sm,_Add_Color.rgb,am),sm.r*clamp(ac.r*particleColor.a*particleColor.a*_Main_Color.a*_Main_Multiply,0.,1.));`;


cafeMaterialShaders.distort1=`
vec2 db=fxUV*distortST.xy+distortST.zw,mb=fxUV*mainST.xy+mainST.zw,kb=fxUV*maskST.xy+maskST.zw;
vec2 du=pair(cd1*_CustomData_DistortTiling_CD1XYXY*db.xyxy)+pair(cd2*_CustomData_DistortTiling_CD2XYXY*db.xyxy)+pair(cd1*_CustomData_DistortOffset_CD1XYXY)+pair(cd2*_CustomData_DistortOffset_CD2XYXY);
vec2 mu=pair(cd1*_CustomData_MainTiling_CD1XYXY*mb.xyxy)+pair(cd2*_CustomData_MainTiling_CD2XYXY*mb.xyxy)+pair(cd1*_CustomData_MainOffset_CD1XYXY)+pair(cd2*_CustomData_MainOffset_CD2XYXY);
vec2 ku=pair(cd1*_CustomData_MaskTiling_CD1XYXY*kb.xyxy)+pair(cd2*_CustomData_MaskTiling_CD2XYXY*kb.xyxy)+pair(cd1*_CustomData_MaskOffset_CD1XYXY)+pair(cd2*_CustomData_MaskOffset_CD2XYXY);
vec2 distortion=sourceTex(distortTex,db+fxTime*vec2(_Dis_Speed_X,_Dis_Speed_Y)+du).rg*(vec2(_Distortion_Power_X,_Distortion_Power_Y)+pair(cd2*_CustomData_DistortPower_CD2XYXY));
vec4 tex=sourceTex(mainTex,mb+mu+fxTime*vec2(_Main_Speed_X,_Main_Speed_Y)+(_Main_Distort_Use!=0.?distortion:vec2(0.)));
float mask=sourceTex(maskTex,kb+ku+fxTime*vec2(_Tex_Mask_Speed_X,_Tex_Mask_Speed_Y)+(_Mask_Distort_Use!=0.?distortion:vec2(0.))).r;
float alpha=clamp((_RGBRGBA!=0.?tex.a:tex.r)*particleColor.a*_Color.a*mask,0.,1.);
if(alpha<_Alphaclip_Value)discard;
diffuseColor=vec4(tex.rgb*particleColor.rgb*_Color.rgb*mask*_Multiply*tex.a,alpha);`;

// Two_Step_Distort_0 PS: R/G are two binary coverage layers, B is alpha.
cafeMaterialShaders.twoStep=`
float distortion=sourceTex(distortTex,fxUV*distortST.xy+distortST.zw+fxTime*vec2(_Dis_Speed_X,_Dis_Speed_Y)).r;
vec2 power=_Custom_Data_Distort_Power_Use!=0.?cd2.xy:vec2(_Dis_Power_X,_Dis_Power_Y);
vec2 uvMain=fxUV*mainST.xy+mainST.zw+distortion*power+fxTime*vec2(_Main_Speed_X,_Main_Speed_Y)+(_Custom_Data_Main_Offset_Use!=0.?cd1.zw:vec2(0.));
vec4 tex=sourceTex(mainTex,uvMain);
float threshold=_Step_Scroll_Use!=0.?cd1.x:_Step_Value;
vec2 coverage=vec2(tex.r>threshold?1.:0.,tex.g>threshold?1.:0.);
float alpha=clamp(coverage.x*_Multiply*particleColor.a*tex.b,0.,1.);
if(alpha<.09)discard;
vec3 base=coverage.x*_Color.rgb*particleColor.rgb;
vec3 highlight=_Color.rgb*_Multiply_G*particleColor.rgb*cd1.y;
diffuseColor=vec4(mix(base,highlight,coverage.y)*_Multiply,alpha);`;

const waterBody=`
vec2 dis=sourceTex(distortTex,fxUV*distortST.xy+distortST.zw+fxTime*vec2(_Dis_Speed_X,_Dis_Speed_Y)+vec2(0.,1.)).rg;
dis*=vec2(_Distortion_Power_X,_Distortion_Power_Y)+(_Custom_Data_Distort_Power_Offset_Use!=0.?cd2.zw:vec2(0.));
float uvAdd=_UV_Add_Use!=0.?dot(fxUV*_UV_Add_TilingOffset.xy+_UV_Add_TilingOffset.zw,vec2(1.)):1.;
vec2 mb=fxUV*mainST.xy+mainST.zw;mb.x*=cd1.w;
vec2 offset=_Custom_Data_MainRB_Offset_Use!=0.?cd2.xy:fxTime*vec2(_Main_Speed_X,_Main_Speed_Y);
vec4 tex=sourceTex(mainTex,mb+offset+dis*uvAdd);
float bThreshold=_BCustom_Data_Use!=0.?cd1.y:_BDisappear_Offset;
float gThreshold=_GCustom_Data_Use!=0.?cd1.x:_GDisappear_Offset;
float shadowValue=_Custom_Data_Shadow_Value_Use!=0.?cd1.z:_Shadow_Value;
float sub=sourceTex(maskTex,fxUV*maskST.xy+maskST.zw+fxTime*vec2(_Sub_Speed_X,_Sub_Speed_Y)+dis*uvAdd).g;
float highlight=clamp((clamp(tex.g+sub,0.,1.)-gThreshold)*_GColor_Sharpness,0.,1.);
vec3 base=tex.r*particleColor.rgb*_MainColor.rgb;
`;
cafeMaterialShaders.water=waterBody+`
float alpha=clamp((tex.b>bThreshold?1.:0.)*particleColor.a*_Mutiply*_MainColor.a*tex.a,0.,1.);
if(alpha<_AlphaClip_Value)discard;
float shadow=tex.b+shadowValue<bThreshold?1.:0.;
diffuseColor=vec4(mix(base,_SubColor.rgb,min(1.,highlight+shadow))*_Mutiply,alpha);`;
cafeMaterialShaders.waterBlur=waterBody+`
float alpha=clamp(clamp((tex.b-bThreshold)*_BColor_Sharpness,0.,1.)*_Mutiply*particleColor.a*_MainColor.a*tex.a,0.,1.);
if(alpha<_AlphaClip_Value)discard;
float shadow=clamp((bThreshold-tex.b-shadowValue)*_Shadow_Glow_Value,0.,1.);
diffuseColor=vec4(mix(base,_SubColor.rgb,min(1.,highlight+shadow))*_Mutiply,alpha);`;

cafeMaterialShaders.step1=cafeMaterialShaders.distort1.slice(0,cafeMaterialShaders.distort1.indexOf('vec2 distortion='))+`
vec2 distortion=sourceTex(distortTex,db+fract(fxTime*vec2(_Dis_Speed_X,_Dis_Speed_Y))+du).rg*(vec2(_Distortion_Power_X,_Distortion_Power_Y)+pair(cd2*_CustomData_DistortPower_CD2XYXY));
distortion*=_UV_Add_Use!=0.?dot(fxUV*_UV_Add_TilingOffset.xy+_UV_Add_TilingOffset.zw,vec2(1.)):1.;
float threshold=_Step_Power+dot(cd1,_CustomData_StepValue_CD1XYXY);
float mask=sourceTex(maskTex,kb+ku+fxTime*vec2(_Mask_Speed_X,_Mask_Speed_Y)+(_Mask_Distort_Use!=0.?distortion:vec2(0.))).r;
float coverage=step(threshold,mask);
vec4 tex=sourceTex(mainTex,mb+mu+fxTime*vec2(_Main_Speed_X,_Main_Speed_Y)+(_Main_Distort_Use!=0.?distortion:vec2(0.)));
float alpha=clamp(coverage*_Color.a*_Multiply*(_RGBRGBA!=0.?tex.a:tex.r)*(_Step_Vertex_Alpha_Use!=0.?1.:particleColor.a),0.,1.);
if(alpha<_Alphaclip_Value)discard;
diffuseColor=vec4(coverage*tex.rgb*_Multiply*tex.a*particleColor.rgb*_Color.rgb,alpha);`;

cafeMaterialShaders.doubleSoft=`
vec2 rb=fxUV*_RTilingxyOffsetzw.xy+_RTilingxyOffsetzw.zw,gb=fxUV*_GTilingxyOffsetzw.xy+_GTilingxyOffsetzw.zw;
vec2 ro=pair(cd1*_CustomData_DistortTilingR_CD1XYXY*rb.xyxy)+pair(cd2*_CustomData_DistortTilingR_CD2XYXY*rb.xyxy)+pair(cd1*_CustomData_DistortOffsetR_CD1XYXY)+pair(cd2*_CustomData_DistortOffsetR_CD2XYXY);
vec2 go=pair(cd1*_CustomData_DistortTilingG_CD1XYXY*gb.xyxy)+pair(cd2*_CustomData_DistortTilingG_CD2XYXY*gb.xyxy)+pair(cd1*_CustomData_DistortOffsetG_CD1XYXY)+pair(cd2*_CustomData_DistortOffsetG_CD2XYXY);
vec2 dr=sourceTex(distortTex,rb+ro+fract(fxTime*vec2(_RDistort_Speed_X,_RDistort_Speed_Y))).rr*(vec2(_RDistort_Power_X,_RDistort_Power_Y)+pair(cd2*_CustomData_DistortPowerR_CD2XYXY));
vec2 dg=sourceTex(distortTex,gb+go+fract(fxTime*vec2(_GDistort_Speed_X,_GDistort_Speed_Y))).gg*(vec2(_GDistort_Power_X,_GDistort_Power_Y)+pair(cd2*_CustomData_DistortPowerG_CD2XYXY));
vec2 mb=fxUV*mainST.xy+mainST.zw,kb=fxUV*maskST.xy+maskST.zw;
vec2 mo=pair(cd1*_CustomData_MainTiling_CD1XYXY*mb.xyxy)+pair(cd2*_CustomData_MainTiling_CD2XYXY*mb.xyxy)+pair(cd1*_CustomData_MainOffset_CD1XYXY)+pair(cd2*_CustomData_MainOffset_CD2XYXY);
vec2 ko=pair(cd1*_CustomData_MaskTiling_CD1XYXY*kb.xyxy)+pair(cd2*_CustomData_MaskTiling_CD2XYXY*kb.xyxy)+pair(cd1*_CustomData_MaskOffset_CD1XYXY)+pair(cd2*_CustomData_MaskOffset_CD2XYXY);
vec4 tex=sourceTex(mainTex,mb+mo+fxTime*vec2(_Main_Speed_X,_Main_Speed_Y)+(_Tex_Main_Distort==1.?dr:_Tex_Main_Distort==2.?dg:_Tex_Main_Distort==3.?dr+dg:vec2(0.)));
float mask=sourceTex(maskTex,kb+ko+fxTime*vec2(_Mask_Speed_X,_Mask_Speed_Y)+(_Tex_Mask_Distort==1.?dr:_Tex_Mask_Distort==2.?dg:_Tex_Mask_Distort==3.?dr+dg:vec2(0.))).r;
float alpha=clamp((_RGBRGBA!=0.?tex.a:tex.r)*particleColor.a*_Color.a*_Multiply*mask,0.,1.);
float sceneDepth=mix(fxDepthRange.x,fxDepthRange.y,texture2D(fxDepthTex,gl_FragCoord.xy/fxDepthSize).r);
alpha*=clamp(((sceneDepth-fxEyeDepth)/max(fxUnitScale,.00001)-_SoftParticleNearFade)/max(.00001,_SoftParticleFarFade-_SoftParticleNearFade),0.,1.);
if(alpha<_Alphaclip_Value)discard;
diffuseColor=vec4(tex.rgb*_Color.rgb*_Multiply*particleColor.rgb,alpha);`;

// Non-soft native variant: the D3D fragment squares vertex alpha and
// multiplies RGB by the main alpha and mask, without a scene-depth fade.
cafeMaterialShaders.doubleDistort=cafeMaterialShaders.doubleSoft.slice(0,cafeMaterialShaders.doubleSoft.indexOf('float alpha='))+`
float alpha=clamp((_RGBRGBA!=0.?tex.a:tex.r)*particleColor.a*particleColor.a*_Color.a*_Multiply*mask,0.,1.);
if(alpha<_Alphaclip_Value)discard;
diffuseColor=vec4(tex.rgb*tex.a*mask*_Color.rgb*_Multiply*particleColor.rgb,alpha);`;

cafeMaterialShaders.distortSoft=cafeMaterialShaders.distort+`
float fade=1.;
if(_SoftParticlesN>0.||_SoftParticlesInvFN>0.){
 float sceneDepth=mix(fxDepthRange.x,fxDepthRange.y,texture2D(fxDepthTex,gl_FragCoord.xy/fxDepthSize).r);
 fade=clamp(((sceneDepth-fxEyeDepth)/max(fxUnitScale,.00001)-_SoftParticlesN)*_SoftParticlesInvFN,0.,1.);
}
diffuseColor*=fade;`;

cafeMaterialShaders.unlit=`diffuseColor=sourceTex(mainTex,fxUV*mainST.xy+mainST.zw)*_Color;`;
cafeMaterialShaders.unlitVC=`diffuseColor=sourceTex(mainTex,fxUV*mainST.xy+mainST.zw)*_Color*particleColor;`;

// Original FX_SHADER_Matcap ps_4_0: main RGB * tint * vertex RGB *
// view-normal matcap RGB. Coverage comes from matcap alpha, not main alpha.
cafeMaterialShaders.matcap=`
vec4 mainSample=sourceTex(mainTex,fxUV*mainST.xy+mainST.zw);
vec4 cap=sourceTex(maskTex,fxViewNormal.xy*.5+.5);
diffuseColor=vec4(mainSample.rgb*_Main_Color.rgb*particleColor.rgb*cap.rgb,cap.a*particleColor.a*_Main_Color.a);`;
cafeMaterialShaders.matcapBlend=cafeMaterialShaders.matcap;
