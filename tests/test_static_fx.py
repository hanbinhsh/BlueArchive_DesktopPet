import sys,unittest
from pathlib import Path
from types import SimpleNamespace as N
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from furniture_water_fx import adapt_water_fx
from furniture_tint import adapt_simple_tint
from static_fx_meshes import attach_static_particles

class StaticFXTests(unittest.TestCase):
 def test_static_only_effect_keeps_authored_mesh_without_particle_sibling(self):
  surface={'path':'/bath/water','staticRenderer':True,'renderer':{'m_Enabled':True},'mesh':{'positions':[[0,0,0],[1,0,0],[0,0,1]]},'children':[]}
  effect={'children':[surface]};mesh=surface['mesh']
  attach_static_particles(effect,12)
  self.assertIs(surface['mesh'],mesh)
  self.assertEqual(surface['renderer']['m_RenderMode'],4)
  self.assertEqual(surface['particle']['InitialModule']['startSize']['scalar'],1)
  self.assertEqual(surface['particle']['EmissionModule']['m_Bursts'][0]['countCurve']['scalar'],1)
  self.assertFalse(surface['particle']['ShapeModule']['enabled'])
 def test_foam_below_transparent_queue_uses_native_mask_not_opaque_color(self):
  texture=N(image=Image.new('RGBA',(2,2),(255,255,255,128)),m_TextureSettings=N(m_WrapU=0,m_WrapV=1))
  tex=N(m_Texture=N(m_PathID=123,read=lambda:texture),m_Scale=N(x=2,y=3),m_Offset=N(x=.1,y=.2))
  original=N(m_Name='FX_MAT_Cafe_Minipool_1',m_CustomRenderQueue=2999,m_Shader=N(read=lambda:N(m_ParsedForm=N(m_Name='DSFX/FX_SHADER_Step_Distort_0',m_SubShaders=[N(m_Passes=[N(m_State=None)])]))),m_SavedProperties=N(m_Floats=[('_SrcBlend',1),('_DstBlend',0),('_ZWrite_Mode',0)],m_Colors=[('_Color',N(r=2,g=2,b=2,a=1))],m_TexEnvs=[(k,tex)for k in ['_Tex_Main','_Tex_Mask','_Tex_Distort']]))
  material=dict(name=original.m_Name,alphaMode='OPAQUE');doc={'bufferViews':[]};binary=bytearray()
  self.assertTrue(adapt_water_fx(original,material,doc,binary))
  self.assertEqual(material['alphaMode'],'BLEND');self.assertFalse(material['extras']['BA_depthWrite'])
  self.assertEqual(material['extras']['BA_sourceRenderQueue'],2999)
  self.assertEqual(material['extras']['BA_waterFx']['maskTexture']['st'],[2,3,.1,.2])
  self.assertEqual(len(doc['images']),3);self.assertGreater(len(binary),0)
 def test_simple_shader_uses_declared_tint_not_stale_white_color(self):
  original=N(m_Shader=N(read=lambda:N(m_ParsedForm=N(m_Name='MX/C-Simple'))),m_SavedProperties=N(m_Colors=[('_Tint',N(r=.84,g=.2,b=.1,a=1)),('_Color',N(r=1.5,g=1.5,b=1.5,a=1))]))
  material={'pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1]},'alphaMode':'OPAQUE'}
  self.assertTrue(adapt_simple_tint(original,material))
  self.assertEqual(material['pbrMetallicRoughness']['baseColorFactor'],[.84,.2,.1,1])
  self.assertEqual(material['alphaMode'],'OPAQUE')

if __name__=='__main__':unittest.main()
