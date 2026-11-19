from pathlib import Path
import UnityPy,json
from glb import load
env=UnityPy.load(*map(str,Path('.assets/selected').glob('*.bundle')))
rows=[];roots=[]
def inspect(go):
 result=[]
 for c in go.m_Component:
  o=c.component.deref()
  if o.type.name=='SkinnedMeshRenderer':
   r=o.read();result.append(dict(name=go.m_Name,mesh=r.m_Mesh.m_PathID,materials=[p.m_PathID for p in r.m_Materials]))
  if o.type.name=='Transform':
   for p in o.read().m_Children:result.extend(inspect(p.read().m_GameObject.read()))
 return result
for o in list(env.objects):
 if o.type.name=='GameObject'and o.read().m_Name=='My_Hotsprings_01_Chair':roots.append(dict(source=o.assets_file.name,sourceBundle=o.assets_file.parent.name,renderers=inspect(o.read())))
for o in list(env.objects):
 if o.type.name!='SkinnedMeshRenderer':continue
 r=o.read()
 if r.m_Mesh.m_PathID:continue
 go=r.m_GameObject.read()
 t=next(c.component.read()for c in go.m_Component if c.component.deref().type.name=='Transform')
 parents=[];p=t
 while p.m_Father.m_PathID:
  p=p.m_Father.read();parents.append(p.m_GameObject.read().m_Name)
 if any('Hotsprings_01_Chair' in n for n in parents):
  rows.append(dict(name=go.m_Name,parents=parents,active=go.m_IsActive,enabled=r.m_Enabled,meshId=r.m_Mesh.m_PathID,materials=[x.m_PathID for x in r.m_Materials]))
Path('test-results/tomoe14-null-renderers.json').write_text(json.dumps(dict(nulls=rows,roots=roots),indent=2),'utf8');print(roots)
