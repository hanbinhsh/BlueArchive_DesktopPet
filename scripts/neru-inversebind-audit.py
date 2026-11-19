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

from UnityPy.helpers.MeshHelper import MeshHandler
from glb import load,read_accessor
import numpy as np

for obj in env.objects:
 if obj.type.name!='SkinnedMeshRenderer':continue
 r=obj.read()
 if r.m_GameObject.read().m_Name!='CH0280_Body' or '_mxload-prefabs-' not in r.object_reader.assets_file.parent.name:continue
 d,b=load(R/'characters/neru_uniform/model.glb');node=next(n for n in d['nodes'] if n.get('name')=='CH0280_Body' and 'mesh' in n);skin=d['skins'][node['skin']]
 names=[d['nodes'][i]['name'] for i in skin['joints']];binds=read_accessor(d,b,skin['inverseBindMatrices']);fix=[]
 for joint,bone in enumerate(r.m_Bones):
  name=bone.read().m_GameObject.read().m_Name
  if name not in names:continue
  orig=r.m_Mesh.read().m_BindPose[joint]
  source=np.array([[getattr(orig,f'e{i}{j}') for j in range(4)] for i in range(4)]);flip=np.diag([-1,1,1,1]);expected=flip@source@flip
  actual=np.array(binds[names.index(name)]).reshape((4,4)).T
  error=float(np.max(np.abs(expected-actual)))
  if 'hair_F' in name or error>.001:fix.append({'name':name,'error':error,'source':expected.tolist(),'actual':actual.tolist()})
 (R/'test-results/neru-inversebind-1029.json').write_text(json.dumps(fix,indent=2),'utf8');print([(f['name'],f['error']) for f in fix])
