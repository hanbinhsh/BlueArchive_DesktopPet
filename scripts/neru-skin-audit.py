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
 if r.m_GameObject.read().m_Name!='CH0280_Body':continue
 h=MeshHandler(r.m_Mesh.read());h.process()
 print('SOURCE',r.object_reader.assets_file.parent.name,len(h.m_Vertices),str(h.m_BoneIndices[:5]),str(h.m_BoneWeights[:5]) if h.m_BoneWeights else None)
 print('BIND',r.m_Mesh.read().m_BindPose[:1])
 print('BONES',[b.read().m_GameObject.read().m_Name for b in r.m_Bones])
 d,b=load(R/'characters/neru_uniform/model.glb')
 node=next(n for n in d['nodes'] if n.get('name')=='CH0280_Body' and 'mesh' in n)
 skin=d['skins'][node['skin']];names=[d['nodes'][i]['name'] for i in skin['joints']]
 bypos={}
 for i,v in enumerate(h.m_Vertices):bypos.setdefault(tuple(round(x,5) for x in (-v[0],v[1],v[2])),[]).append(i)
 mismatches=[];total=0
 for pr in d['meshes'][node['mesh']]['primitives']:
  pos=read_accessor(d,b,pr['attributes']['POSITION']);j=read_accessor(d,b,pr['attributes']['JOINTS_0']);w=read_accessor(d,b,pr['attributes']['WEIGHTS_0'])
  for i,v in enumerate(pos):
   candidates=bypos.get(tuple(round(x,5) for x in v),[])
   if not candidates:continue
   actual={names[bi]:weight for bi,weight in zip(j[i],w[i]) if weight>.0001}
   expected=[{r.m_Bones[bi].read().m_GameObject.read().m_Name:weight for bi,weight in zip(h.m_BoneIndices[k],h.m_BoneWeights[k] if h.m_BoneWeights else [1]) if weight>.0001} for k in candidates]
   if not any(set(e)==set(actual) and all(abs(e[n]-actual[n])<.001 for n in e) for e in expected):mismatches.append({'v':i,'actual':actual,'expected':expected})
   total+=1
 print('COMPARE',total,len(mismatches),mismatches[:8])
