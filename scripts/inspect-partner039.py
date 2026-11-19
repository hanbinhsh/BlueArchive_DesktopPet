from pathlib import Path
import json,UnityPy
files=[p for p in Path('.assets/selected').glob('*.bundle')if'ch0346-'in p.name];env=UnityPy.load(*map(str,files));rows=[]
def walk(go,active=True):
 active=active and bool(go.m_IsActive);out=[]
 for c in go.m_Component:
  o=c.component.deref()
  if o.type.name in ['MeshRenderer','SkinnedMeshRenderer']:
   r=o.read();out.append({'node':go.m_Name,'active':active,'enabled':bool(r.m_Enabled)})
  if o.type.name=='Transform':
   for ch in o.read().m_Children:out.extend(walk(ch.read().m_GameObject.read(),active))
 return out
for o in env.objects:
 if o.type.name=='GameObject':
  go=o.read()
  if go.m_Name in ['CH0346','Cafe_CH0346']:rows.append({'root':go.m_Name,'renderers':walk(go),'cab':o.assets_file.name})
 if o.type.name=='AnimationClip':
  clip=o.read()
  if'my_event094'in clip.m_Name or clip.m_Name.endswith('Cafe_Idle'):rows.append({'clip':clip.m_Name,'events':[{'time':e.time,'function':e.functionName,'int':e.intParameter}for e in clip.m_Events]})
Path('test-results/partner039-source-visibility.json').write_text(json.dumps(rows,indent=2),'utf8');print(json.dumps(rows,indent=2))
