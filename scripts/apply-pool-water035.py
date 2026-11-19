"""Restore the original MX/Water textures and material equations (D3D evidence)."""
import pathlib,sys,json,io,UnityPy
from source_dependencies import resolve_cached
from glb import load,save,append_view,compact
env=UnityPy.load(*map(str,pathlib.Path('.assets/selected').glob('*pool_party-pool-*.bundle')))
materials={o.read().m_Name:o.read() for o in env.objects if o.type.name=='Material'}
report=[]
for p in pathlib.Path(sys.argv[1]).glob('*/f*.glb'):
 d,b=load(p);changed=[]
 for m in d['materials']:
  original=materials.get(m.get('name'))
  if original is None:continue
  shader=resolve_cached(env,original.m_Shader.read)
  if shader.m_ParsedForm.m_Name!='MX/Water':continue
  spec={'floats':dict(original.m_SavedProperties.m_Floats),'colors':{k:[v.r,v.g,v.b,v.a] for k,v in original.m_SavedProperties.m_Colors}}
  for slot,t in original.m_SavedProperties.m_TexEnvs:
   if slot not in ['_FoamMaskTex','_FoamTex','_WaveTex'] or not t.m_Texture.m_PathID:continue
   texture=resolve_cached(env,t.m_Texture.read);buf=io.BytesIO();texture.image.save(buf,format='PNG');im=len(d.setdefault('images',[]));d['images'].append({'bufferView':append_view(d,b,buf.getvalue()),'mimeType':'image/png'})
   sampler=len(d.setdefault('samplers',[]));wrap=lambda x:10497 if x==0 else 33648 if x==2 else 33071
   d['samplers'].append({'wrapS':wrap(texture.m_TextureSettings.m_WrapU),'wrapT':wrap(texture.m_TextureSettings.m_WrapV)})
   ix=len(d.setdefault('textures',[]));d['textures'].append({'source':im,'sampler':sampler});spec[slot]={'index':ix,'srgb':texture.m_ColorSpace==1,'st':[t.m_Scale.x,t.m_Scale.y,t.m_Offset.x,t.m_Offset.y]}
  assert all(k in spec for k in ['_FoamMaskTex','_FoamTex','_WaveTex'])
  m['pbrMetallicRoughness']={'baseColorFactor':[1,1,1,1],'roughnessFactor':1,'metallicFactor':0};m['extras']['BA_poolWater']=spec;m['extras']['BA_depthWrite']=True
  queue=original.m_CustomRenderQueue if original.m_CustomRenderQueue>=0 else 3000
  m['extras'].update(BA_sourceRenderQueue=queue,BA_renderOrder=queue*1000000)
  changed.append(m['name'])
 if changed:save(p,d,compact(d,b));report.append({'file':str(p),'materials':changed})
pathlib.Path('test-results/poolwater035-applied.json').write_text(json.dumps(report,indent=2),'utf8');print(report)
