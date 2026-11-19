import json,pathlib,hashlib
import UnityPy
R=pathlib.Path(__file__).resolve().parents[1];W=R/'.assets';out=W/'visual-triage-1029';out.mkdir(exist_ok=True)
files={p.name:p for folder in ['selected','costume-audit','costume-variants'] for p in (W/folder).glob('*.bundle')};env=UnityPy.load(*map(str,files.values()));targets={'CH0280':'neru_uniform','CH0174':'otogi','my_event062_icepool':'eimi_pool','my_event090_electronicgate':'akane_gate'};report={}
def walk(go,rows):
 for item in go.m_Component:
  kind=item.component.deref().type.name;c=item.component.read()
  if kind=='Transform':
   for child in c.m_Children:walk(child.read().m_GameObject.read(),rows)
  if kind not in ['MeshRenderer','SkinnedMeshRenderer']:continue
  mats=[]
  for ptr in c.m_Materials:
   if not ptr.m_PathID:continue
   m=ptr.read();tex=[]
   for k,v in m.m_SavedProperties.m_TexEnvs:
    if not v.m_Texture.m_PathID:continue
    t=v.m_Texture.read();im=t.image;fname=m.m_Name+'-'+k+'.png';im.save(out/fname)
    tex.append({'slot':k,'name':t.m_Name,'size':im.size,'scale':[v.m_Scale.x,v.m_Scale.y],'offset':[v.m_Offset.x,v.m_Offset.y],'file':fname,'source':t.object_reader.assets_file.name,'path':t.object_reader.path_id})
   mats.append({'name':m.m_Name,'shader':m.m_Shader.read().m_Name if m.m_Shader.m_PathID else None,'floats':dict(m.m_SavedProperties.m_Floats),'colors':{k:[v.r,v.g,v.b,v.a] for k,v in m.m_SavedProperties.m_Colors},'textures':tex})
  rows.append({'renderer':go.m_Name,'type':kind,'materials':mats})
trees={}
for o in env.objects:
 if o.type.name!='GameObject':continue
 go=o.read()
 if go.m_Name not in targets:continue
 key=targets[go.m_Name];rows=[];walk(go,rows)
 transforms=[];components=[]
 def visit(g):
  for cp in g.m_Component:
   obj=cp.component.deref();kind=obj.type.name
   if kind=='Transform':
    t=obj.read();transforms.append({'name':g.m_Name,'pathID':obj.path_id,'rotation':[t.m_LocalRotation.x,t.m_LocalRotation.y,t.m_LocalRotation.z,t.m_LocalRotation.w],'position':[t.m_LocalPosition.x,t.m_LocalPosition.y,t.m_LocalPosition.z]})
    for child in t.m_Children:visit(child.read().m_GameObject.read())
   elif kind=='MonoBehaviour':components.append({'go':g.m_Name,'data':obj.read_typetree()})
 visit(go);trees.setdefault(key,[]).append({'file':go.object_reader.assets_file.parent.name,'renderers':rows,'transforms':transforms,'components':components})
(R/'test-results/source-detail-1029.json').write_text(json.dumps(trees,ensure_ascii=False,indent=2),'utf8')
print({k:len(v) for k,v in trees.items()})
