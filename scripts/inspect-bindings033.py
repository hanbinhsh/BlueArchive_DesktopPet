from pathlib import Path
import UnityPy,json,sys
sys.path.insert(0,'scripts');from source_dependencies import resolve_cached
files=[p for p in Path('.assets/selected').glob('*.bundle') if p.name.startswith('cafe-') and '-prefabs-' in p.name]
e=UnityPy.load(*map(str,files));read=lambda p:resolve_cached(e,p.read)
names=['My_Hotsprings_01_Massagechair','my_event06_hotspringswindow','my_event20_prayerchair'];out=[]
def visit(go):
 parts=[read(c.component) for c in go.m_Component];t=next(c for c in parts if c.object_reader.type.name=='Transform')
 return {'name':go.m_Name,'position':t.m_LocalPosition.__dict__ if hasattr(t.m_LocalPosition,'__dict__') else [t.m_LocalPosition.x,t.m_LocalPosition.y,t.m_LocalPosition.z],'components':[{'type':c.object_reader.type.name,'data':c.object_reader.read_typetree()} for c in parts if c.object_reader.type.name not in ['Transform','MeshFilter','MeshRenderer','SkinnedMeshRenderer']], 'children':[visit(read(read(c).m_GameObject)) for c in t.m_Children]}
for o in list(e.objects):
 if o.type.name=='PlayableDirector':
  d=o.read();g=read(d.m_GameObject)
  if g.m_Name in names:out.append(visit(g))
Path('test-results/bindings033-hierarchy.json').write_text(json.dumps(out,indent=2,default=str),'utf8')
def show(n,d=0):
 print(' '*d+n['name'],n['position'],[c['type'] for c in n['components']]);
 for c in n['children']:show(c,d+1)
for n in out:show(n)
