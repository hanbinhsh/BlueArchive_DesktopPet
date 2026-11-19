"""Inspect actual FxBillboard components, rather than guessing by node names."""
import pathlib,json,UnityPy,sys
from source_dependencies import resolve_cached
source=json.loads(pathlib.Path('.assets/cafe-fx-all033/source.json').read_text('utf8'))
icons=[t['icon'].lower() for t in source['timelines']]
env=UnityPy.load(*map(str,[p for p in pathlib.Path('.assets/selected').glob('*.bundle') if any(i in p.name.lower() for i in icons)]))
wanted={k.removesuffix('__existing') for k in source['effects']};out=[];seen=set()
def read(p):return resolve_cached(env,p.read)
def walk(go,path):
 path+='/'+go.m_Name
 for c in go.m_Component:
  obj=resolve_cached(env,c.component.deref)
  if obj.type.name=='MonoBehaviour':
   v=obj.read()
   if read(v.m_Script).m_ClassName=='FxBillboard':
    data=obj.read_typetree()
    if data.get('m_Enabled') and path not in seen:out.append({'path':path,'fixedY':bool(data['FixedY'])});seen.add(path)
  elif obj.type.name=='Transform':
   for child in obj.read().m_Children:walk(read(read(child).m_GameObject),path)
for o in list(env.objects):
 if o.type.name=='GameObject' and o.read().m_Name in wanted:walk(o.read(),'')
pathlib.Path('.assets/fx-billboards035.json').write_text(json.dumps(out,indent=2),'utf8')
print('Authored billboard groups',len(out))
