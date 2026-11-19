import json,pathlib,hashlib
import UnityPy
R=pathlib.Path(__file__).resolve().parents[1];W=R/'.assets';out=W/'visual-triage';out.mkdir(exist_ok=True)
files={p.name:p for folder in ['selected','costume-audit','costume-variants'] for p in (W/folder).glob('*.bundle')};env=UnityPy.load(*map(str,files.values()));targets={'CH0288':'aoba','CH0163':'chinatsu_onsen','CH0280':'neru_uniform'};report={}
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
for o in env.objects:
 if o.type.name!='MonoBehaviour':continue
 d=o.read_typetree()
 if 'MouthDefaultUV' not in d or not d.get('MouthRenderer',{}).get('m_PathID'):continue
 go=o.read().m_GameObject.read()
 if go.m_Name not in targets:continue
 rows=[];walk(go,rows);report[targets[go.m_Name]]={'defaultUV':d['MouthDefaultUV'],'renderers':rows};print(targets[go.m_Name],len(rows),flush=True)
(R/'test-results/visual-triage-source.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
