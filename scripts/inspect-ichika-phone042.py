"""Inspect original character-embedded phone UI, separate from chair Timeline FX."""
from pathlib import Path
import json,UnityPy
from source_dependencies import resolve_cached
W=Path('.assets');files=[p for p in(W/'selected').glob('*.bundle')if'characters-ch0071-'in p.name or p.name.startswith('character-ch0071-')or p.name.startswith('cafe-')and'-prefabs-'in p.name]
env=UnityPy.load(*map(str,files));rows=[]
def read(p):return resolve_cached(env,p.read)
def walk(go,path='',parentsActive=True):
 path+='/'+go.m_Name;parts={c.component.deref().type.name:c.component.deref()for c in go.m_Component};t=parts['Transform'].read();rows.append(dict(path=path,active=bool(go.m_IsActive),hierarchyActive=parentsActive and bool(go.m_IsActive),components=list(parts),position=[t.m_LocalPosition.x,t.m_LocalPosition.y,t.m_LocalPosition.z],rotation=[t.m_LocalRotation.x,t.m_LocalRotation.y,t.m_LocalRotation.z,t.m_LocalRotation.w],scale=[t.m_LocalScale.x,t.m_LocalScale.y,t.m_LocalScale.z],source=go.object_reader.assets_file.name,id=go.object_reader.path_id))
 if'ParticleSystemRenderer'in parts:
  r=parts['ParticleSystemRenderer'].read();rows[-1]['renderer']=parts['ParticleSystemRenderer'].read_typetree();rows[-1]['materials']=[]
  for p in r.m_Materials:
   if not p.m_PathID:continue
   m=read(p);rows[-1]['materials'].append(dict(name=m.m_Name,shader=read(m.m_Shader).m_ParsedForm.m_Name,textures=[dict(slot=k,name=read(tex.m_Texture).m_Name)for k,tex in m.m_SavedProperties.m_TexEnvs if tex.m_Texture.m_PathID]))
 if'ParticleSystem'in parts:
  p=parts['ParticleSystem'].read_typetree();rows[-1]['particle']={k:p[k]for k in ['lengthInSec','looping','prewarm','startDelay','moveWithTransform','InitialModule','EmissionModule','ShapeModule']}
 if'PlayableDirector'in parts:rows[-1]['director']=parts['PlayableDirector'].read_typetree()
 for child in t.m_Children:walk(read(read(child).m_GameObject),path,parentsActive and bool(go.m_IsActive))
for o in list(env.objects):
 if o.type.name!='GameObject':continue
 go=o.read()
 if go.m_Name=='FX_my_autumnsports_01_chair_03_Phone_Emo_01':
  t=next(c.component.read()for c in go.m_Component if c.component.deref().type.name=='Transform');parents=[]
  while t.m_Father.m_PathID:t=read(t.m_Father);parents.append(read(t.m_GameObject).m_Name)
  walk(go,'/'.join(reversed(parents)))
Path('test-results/ichika042-phone-source-inspection.json').write_text(json.dumps(rows,indent=2),'utf8')
for r in rows:print(r['path'],r['active'],r['components'],r.get('materials',''))
