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

seen=set();result=[]
for o in env.objects:
 if o.type.name!='Material':continue
 m=o.read()
 if not m.m_Name.startswith('FX_MAT_Cafe_Icepool') and m.m_Name!='FX_MAT_Cafe_LED_07':continue
 shader=m.m_Shader.read();d=shader.object_reader.read_typetree();key=shader.object_reader.path_id
 if key in seen:continue
 seen.add(key);result.append({'material':m.m_Name,'shader':d});print(m.m_Name,key,d.keys(),flush=True)
(R/'test-results/icepool-shaders-1029.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
