"""Read the original mouth atlas transforms for audit suspects (no asset writes)."""
import pathlib,json,UnityPy
from source_dependencies import resolve_cached
root=pathlib.Path('.assets/selected')
ids=['hina_original','ch0063','ch0239','ch0252']
files=[p for p in root.glob('*.bundle') if any('-'+s+'-' in p.name for s in ids) and any(s in p.name for s in ['-materials-','-prefabs-','-meshes-','-textures-'])]
env=UnityPy.load(*map(str,files));rows=[]
for o in list(env.objects):
 if o.type.name!='Material':continue
 m=o.read();slots=dict(m.m_SavedProperties.m_TexEnvs)
 if '_MouthTileTex' not in slots:continue
 t=slots['_MouthTileTex']
 if not t.m_Texture.m_PathID:continue
 tex=resolve_cached(env,t.m_Texture.read)
 row={'material':m.m_Name,'shader':resolve_cached(env,m.m_Shader.read).m_ParsedForm.m_Name,'floats':dict(m.m_SavedProperties.m_Floats),'scale':[t.m_Scale.x,t.m_Scale.y],'offset':[t.m_Offset.x,t.m_Offset.y],'texture':tex.m_Name,'size':[tex.m_Width,tex.m_Height]}
 rows.append(row)
 tex.image.save(pathlib.Path('test-results')/('mouth-source-'+m.m_Name+'.png'))
defaults=[]
for o in list(env.objects):
 if o.type.name!='MonoBehaviour':continue
 d=o.read_typetree()
 if 'MouthDefaultUV' in d:
  defaults.append({'name':resolve_cached(env,o.read().m_GameObject.read).m_Name,'uv':d['MouthDefaultUV']})
print(json.dumps({'materials':rows,'defaults':defaults},indent=2));pathlib.Path('test-results/mouth-source-1105.json').write_text(json.dumps({'materials':rows,'defaults':defaults},indent=2))
