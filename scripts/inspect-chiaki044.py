"""Compare the shipped face renderer layout with the original CH0238 prefab."""
from pathlib import Path
import json,UnityPy,sys
from glb import load
from source_dependencies import resolve_cached
env=UnityPy.load(*map(str,[p for p in Path('.assets/selected').glob('*.bundle')if'ch0238-'in p.name]));rows=[]
def walk(go,path='',active=True):
 active=active and bool(go.m_IsActive);path=(path+'/'+go.m_Name).lstrip('/')
 for c in go.m_Component:
  o=c.component.deref();v=o.read()
  if o.type.name in ['MeshRenderer','SkinnedMeshRenderer']:
   mats=[]
   for ptr in v.m_Materials:
    if not ptr.m_PathID:continue
    m=resolve_cached(env,ptr.read);mats.append(dict(name=m.m_Name,floats=dict(m.m_SavedProperties.m_Floats),colors={k:[v.r,v.g,v.b,v.a]for k,v in m.m_SavedProperties.m_Colors},textures=[dict(slot=k,texture=resolve_cached(env,t.m_Texture.read).m_Name if t.m_Texture.m_PathID else None,scale=[t.m_Scale.x,t.m_Scale.y],offset=[t.m_Offset.x,t.m_Offset.y])for k,t in m.m_SavedProperties.m_TexEnvs]))
   rows.append(dict(path=path,name=go.m_Name,active=active,enabled=v.m_Enabled,materials=mats))
  elif o.type.name=='Transform':
   for child in v.m_Children:walk(child.read().m_GameObject.read(),path,active)
for o in env.objects:
 if o.type.name=='GameObject'and o.read().m_Name=='CH0238':walk(o.read())
d,b=load(Path('characters/chiaki/model.glb'));extras=d['scenes'][0]['extras'];meta=extras['BAAD_unity_animation']['clips']
report=dict(original=rows,visibility=extras['BA_pet_visibility'],clips=[dict(name=c['name'],events=c['events'],unity_curves=c['unity_curves'])for c in meta],meshes=[dict(index=i,name=n.get('name'),mesh=n['mesh'],materials=[d['materials'][p['material']]['name']for p in d['meshes'][n['mesh']]['primitives']])for i,n in enumerate(d['nodes'])if'mesh'in n])
Path('test-results/chiaki044-face-source.json').write_text(json.dumps(report,indent=2),'utf8')
for i,r in enumerate(rows):print(i,r['name'],r['active'],r['enabled'],[m['name']for m in r['materials']])
for c in meta:
 if c['name'].endswith(('Cafe_Idle','Cafe_Reaction','Formation_Pickup')):print(c['name'],c['events'])
