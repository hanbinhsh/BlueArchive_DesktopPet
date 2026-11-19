"""Validate staged resources and prove unchanged character/furniture geometry."""
import json,pathlib,hashlib,sys,math
from glb import load,read_accessor
root=pathlib.Path('.assets/fx035-stage');changes=json.loads(pathlib.Path('test-results/resources035-pending.json').read_text('utf8'));report=[]
def texture_refs(x):
 if not isinstance(x,dict):return
 for k,v in x.items():
  if k.endswith(('Texture','Tex')) and isinstance(v,dict) and 'index'in v:yield v['index']
  else:yield from texture_refs(v)
def geometry(d,b,node):
 mesh=d['meshes'][node['mesh']];result=[]
 for p in mesh['primitives']:
  result.append({**{k:read_accessor(d,b,v) for k,v in p['attributes'].items()},'indices':read_accessor(d,b,p['indices']) if 'indices'in p else None,'morphs':[{k:read_accessor(d,b,v) for k,v in t.items()} for t in p.get('targets',[])]})
 return result
for item in changes:
 rel=pathlib.Path(item['path']);p=root/rel;old=pathlib.Path('characters')/rel
 assert hashlib.sha256(p.read_bytes()).hexdigest()==item['new']
 if p.suffix=='.json':
  before=json.loads(old.read_text('utf8'));after=json.loads(p.read_text('utf8'));angles=[]
  for a,z in zip(before['furniture'],after['furniture']):
   if a.get('yaw')!=z.get('yaw'):angles.append([a['id'],a.get('yaw'),z.get('yaw')]);a['yaw']=z['yaw']
  assert before==after,(rel,'unexpected configuration change');report.append({'path':str(rel),'angles':angles});continue
 d,b=load(p);o,ob=load(old);names={n.get('name'):n for n in d['nodes']};count=0
 for n in o['nodes']:
  if 'mesh' not in n or n.get('name','').startswith(('cafe_fx_','cafe_particle_')):continue
  assert geometry(o,ob,n)==geometry(d,b,names[n['name']]),(rel,n['name'],'base geometry changed');count+=1
 for m in d['materials']:
  for ix in texture_refs(m):assert 0<=ix<len(d.get('textures',[])),(rel,m['name'],'texture',ix)
 for a in d['animations']:
  for ch in a['channels']:
   assert ch['target']['node']<len(d['nodes']);sampler=a['samplers'][ch['sampler']];times=[v[0] for v in read_accessor(d,b,sampler['input'])];assert times==sorted(times)
   assert len(times)==len(read_accessor(d,b,sampler['output'])),(rel,'animation count')
 for v in d.get('bufferViews',[]):assert v.get('byteOffset',0)+v['byteLength']<=len(b)
 assert not any(x.get('uri') for key in ['buffers','images'] for x in d.get(key,[]))
 report.append({'path':str(rel),'unchangedBaseMeshes':count,'particles':sum(bool(m.get('extras',{}).get('BA_cafeParticle')) for m in d['materials']),'sha256':item['new']})
pathlib.Path('test-results/stage035-verification.json').write_text(json.dumps(report,indent=2),'utf8');print('Validated',len(report),'changed files; original geometry unchanged')
