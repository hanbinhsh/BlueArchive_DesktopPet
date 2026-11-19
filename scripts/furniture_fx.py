"""Translate verified texture-masked cafe FX, preserving their authored mask."""
import io
import numpy as np
from PIL import Image
from glb import append_view

def adapt_masked_fx(original, material, doc, binary):
    if original.m_Name not in ('FX_MAT_Cafe_Icepool_Glow', 'FX_MAT_Cafe_LED_07'):
        return False
    shader=original.m_Shader.read().m_ParsedForm.m_Name
    if shader not in ('DSFX/FX_SHADER_AlphaBlend_Add','DSFX/FX_SHADER_AlphaBlend_0'):
        raise ValueError('Unverified cafe FX shader '+shader)
    tex=dict(original.m_SavedProperties.m_TexEnvs)['_Texture']
    source=tex.m_Texture.read().image.convert('RGBA')
    pixels=np.asarray(source).copy()
    floats=dict(original.m_SavedProperties.m_Floats)
    # Additive grayscale textures store their coverage in RGB, not in alpha.
    # GLB has no additive shader: retain the source mask as transparent coverage.
    if shader.endswith('_Add'):
        pixels[:,:,3]=np.maximum.reduce(pixels[:,:,:3],axis=2)
    png=io.BytesIO();Image.fromarray(pixels).save(png,format='PNG')
    image=len(doc.setdefault('images',[]));doc['images'].append({'bufferView':append_view(doc,binary,png.getvalue()),'mimeType':'image/png'})
    texture=len(doc.setdefault('textures',[]));doc['textures'].append({'source':image})
    color=dict(original.m_SavedProperties.m_Colors)['_Color']
    material['pbrMetallicRoughness']={'baseColorTexture':{'index':texture},'baseColorFactor':[max(0,min(1,v)) for v in (color.r,color.g,color.b,color.a)],'metallicFactor':0,'roughnessFactor':1}
    sx,sy=tex.m_Scale.x,tex.m_Scale.y;ox,oy=tex.m_Offset.x,tex.m_Offset.y
    if (sx,sy,ox,oy)!=(1,1,0,0):
        material['pbrMetallicRoughness']['baseColorTexture']['extensions']={'KHR_texture_transform':{'scale':[sx,sy],'offset':[ox,1-sy-oy]}}
        if 'KHR_texture_transform' not in doc.setdefault('extensionsUsed',[]):doc['extensionsUsed'].append('KHR_texture_transform')
    material.update(alphaMode='BLEND',doubleSided=floats.get('_Cull_Mode',2)==0)
    material['extras']={'BA_maskedFx':True,'BA_sourceShader':shader,'BA_sourceTextureProperty':'_Texture','BA_depthWrite':False,'BA_additiveApproximation':shader.endswith('_Add')}
    return True
