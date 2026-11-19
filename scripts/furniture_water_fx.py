"""Retain original DSFX water inputs and render state for the local renderer.

The Step_Distort and Multiplicative equations were checked against the shipped
D3D bytecode (see .assets/water-shaders), rather than the stale _SrcBlend fields
left on these materials. No replacement water geometry is generated.
"""
import io
from glb import append_view

SUPPORTED={
    'DSFX/FX_SHADER_Step_Distort_0':'step',
    'DSFX/FX_SHADER_Multiplicative_0':'multiply',
    'DSFX/FX_SHADER_AlphaBlend_Add_Distort_0':'distort',
    'DSFX/FX_SHADER_Matcap_0':'matcapBlend',
    'DSFX/FX_SHADER_Matcap':'matcap',
}

def adapt_water_fx(original,material,doc,binary):
    # Static foam, beaker liquid, and cup liquids use the same DSFX shaders as particles.
    # A queue of 2999 is transparent too; a name/queue threshold must never
    # convert these meshes into an opaque white fallback.
    tex_envs=dict(original.m_SavedProperties.m_TexEnvs)
    has_main=bool(tex_envs.get('_Tex_Main') and tex_envs['_Tex_Main'].m_Texture.m_PathID)
    has_matcap=bool(tex_envs.get('_Matcap_Tex') and tex_envs['_Matcap_Tex'].m_Texture.m_PathID)
    if not has_main and not has_matcap:return False
    shader=original.m_Shader.read().m_ParsedForm
    kind=SUPPORTED.get(shader.m_Name)
    if not kind:return False
    floats=dict(original.m_SavedProperties.m_Floats)
    colors=dict(original.m_SavedProperties.m_Colors)
    textures=tex_envs
    spec={'kind':kind,'floats':floats}
    if kind in ('matcap','matcapBlend'):
        spec['colors']={k:[getattr(v,c)for c in 'rgba']for k,v in colors.items()}
        slots=[('_Main_Tex','mainTexture'),('_Matcap_Tex','maskTexture')]
    else:
        spec['color']=[getattr(colors['_Color'],k) for k in 'rgba']
        slots=[('_Tex_Main','mainTexture'),('_Tex_Mask','maskTexture'),('_Tex_Distort','distortTexture')]
    for slot,key in slots:
        tex=textures.get(slot)
        if not tex or not tex.m_Texture.m_PathID:continue
        source=tex.m_Texture.read();png=io.BytesIO();source.image.save(png,format='PNG')
        image=len(doc.setdefault('images',[]));doc['images'].append({'bufferView':append_view(doc,binary,png.getvalue()),'mimeType':'image/png'})
        sampler=len(doc.setdefault('samplers',[]));settings=source.m_TextureSettings
        wrap=lambda v:10497 if v==0 else 33648 if v==2 else 33071
        doc['samplers'].append({'wrapS':wrap(settings.m_WrapU),'wrapT':wrap(settings.m_WrapV)})
        index=len(doc.setdefault('textures',[]));doc['textures'].append({'source':image,'sampler':sampler})
        spec[key]={'index':index,'st':[tex.m_Scale.x,tex.m_Scale.y,tex.m_Offset.x,tex.m_Offset.y]}
    if kind in ('matcap','matcapBlend'):assert 'maskTexture' in spec
    else:assert 'mainTexture' in spec
    if kind=='step':assert 'maskTexture' in spec and 'distortTexture' in spec
    state=shader.m_SubShaders[0].m_Passes[0].m_State
    material.update(alphaMode='BLEND',doubleSided=floats.get('_Cull_Mode',2)==0)
    material['pbrMetallicRoughness']={'baseColorFactor':[1,1,1,1],'metallicFactor':0,'roughnessFactor':1}
    material['extensions']={'KHR_materials_unlit':{}}
    queue=original.m_CustomRenderQueue if original.m_CustomRenderQueue>=0 else 3000
    material['extras']={'BA_depthWrite':bool(floats['_ZWrite_Mode']),'BA_maskedFx':True,
        'BA_sourceShader':shader.m_Name,'BA_sourceRenderQueue':queue,'BA_renderOrder':queue*1000000,
        'BA_waterFx':spec}
    if kind in ('distort','matcap','matcapBlend'):
        spec.pop('color',None)
        if 'colors' not in spec:spec['colors']={k:[getattr(v,c)for c in 'rgba']for k,v in colors.items()}
        material['extras'].pop('BA_waterFx');material['extras']['BA_smokeFx']=spec
    return True
