"""Verify new original curves and packed skin, and lock the previous resources."""
import json,hashlib,sys,math
from pathlib import Path
import UnityPy
from UnityPy.helpers.MeshHelper import MeshHandler,unpack_ints
from compressed_skin import decode_packed_skin
from glb import load,read_accessor
R=Path(__file__).resolve().parents[1];T=R/'test-results';stage=R/'.assets/wave14-final'
read=lambda p:json.loads(p.read_text('utf8'))
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
specs=read(R/'scripts/roster-wave14.json');index=read(T/'action-source-index.json');rows=[]
for key in specs:
 c=read(stage/key/'character.json');d,b=load(stage/key/'model.glb');meta={x['track']:x for x in d['scenes'][0]['extras']['BAAD_unity_animation']['clips']};sources=[]
 for entry in index[key]:
  p=R/entry['path'];sd,sb=load(p);sources.append((p,sd,sb,{x['track']:x for x in sd['scenes'][0]['extras']['BAAD_unity_animation']['clips']}))
 curves=0
 for action in c['actions']:
  name=action['clip'];matches=[s for s in sources if s[3].get(name)==meta[name]and any(a['name']==name for a in s[1].get('animations',[]))];assert matches,(key,name)
  source,sd,sb,_=matches[0];a=next(a for a in d['animations']if a['name']==name);sa=next(a for a in sd['animations']if a['name']==name);assert len(a['channels'])==len(sa['channels'])
  for x,y in zip(a['channels'],sa['channels']):
   assert x['target']['path']==y['target']['path']and d['nodes'][x['target']['node']]['name']==sd['nodes'][y['target']['node']]['name']
   xs=a['samplers'][x['sampler']];ys=sa['samplers'][y['sampler']];assert xs.get('interpolation')==ys.get('interpolation')
   for prop in ['input','output']:assert read_accessor(d,b,xs[prop])==read_accessor(sd,sb,ys[prop]),(key,name,prop)
   curves+=1
 assert d['scenes'][0]['extras'].get('BA_halo_follow')
 assert any('halo'in n.get('name','').lower()and'mesh'in n for n in d['nodes'])
 assert not any(x.get('uri')for x in d.get('buffers',[])+d.get('images',[]))
 assert (stage/key/'thumbnail.png').is_file()and c.get('mouth')
 for f in c.get('furniture',[]):
  fd,fb=load(stage/key/f['model']);assert any(a['name']==f['clip']for a in fd['animations']);assert f['duration']>0
  assert not any(x.get('uri')for x in fd.get('buffers',[])+fd.get('images',[]))
 rows.append(dict(character=key,actions=len(c['actions']),furniture=len(c.get('furniture',[])),unchangedAuthoredChannels=curves,modelSha256=sha(stage/key/'model.glb')))
env=UnityPy.load(*map(str,(R/'.assets/selected').glob('*hinata_original-*.bundle')))
renderers=[]
def walk(go):
 for component in go.m_Component:
  obj=component.component.deref()
  if obj.type.name=='SkinnedMeshRenderer'and go.m_Name=='Hinata_Original_Body':renderers.append(obj.read())
  if obj.type.name=='Transform':
   for child in obj.read().m_Children:walk(child.read().m_GameObject.read())
for o in env.objects:
 if o.type.name=='MonoBehaviour'and'MouthDefaultUV'in o.read_typetree()and o.read().m_GameObject.read().m_Name=='Hinata_Original':walk(o.read().m_GameObject.read())
renderer=renderers[-1]
source=MeshHandler(renderer.m_Mesh.read());source.process();packed=source.src.m_CompressedMesh
weights,bones=decode_packed_skin(unpack_ints(packed.m_Weights),unpack_ints(packed.m_BoneIndices),len(source.m_Vertices))
d,b=load(stage/'hinata/model.glb');node=next(n for n in d['nodes']if n.get('name')=='Hinata_Original_Body'and'mesh'in n)
joint_names=[d['nodes'][i]['name']for i in d['skins'][node['skin']]['joints']];remap=[joint_names.index(p.read().m_GameObject.read().m_Name)for p in renderer.m_Bones]
count=0
for p in d['meshes'][node['mesh']]['primitives']:
 actual=read_accessor(d,b,p['attributes']['WEIGHTS_0']);indices=read_accessor(d,b,p['attributes']['JOINTS_0']);assert len(actual)==len(weights)
 for w,a,j,ix in zip(weights,actual,bones,indices):
  assert max(abs(x-y)for x,y in zip(w,a))<1e-6,(w,a)
  assert all(remap[v]==target for v,target,weight in zip(j,ix,w)if weight>0),(j,ix,w,[(renderer.m_Bones[v].read().m_GameObject.read().m_Name,joint_names[target])for v,target,weight in zip(j,ix,w)if weight>0])
 count+=len(actual)
assert sum(any(v<0 for v in row)for row in source.m_BoneWeights)==318
previous=read(T/'release039-resources.json')
for item in previous:assert sha(R/'characters'/item['path'])==item['sha256'],item['path']
framing=[r for r in read(T/'expanded-framing.json')if r['character']in specs]
(T/'wave14-framing.json').write_text(json.dumps(framing,indent=2),'utf8')
report=dict(added=rows,baseVersion='0.2.18',unchangedPreviousFiles=len(previous),nativeHinataVertices=len(weights),verifiedSkinVertexRecords=count,correctedPackedWeights=318)
(T/'wave14-resources.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps(report,indent=2))
