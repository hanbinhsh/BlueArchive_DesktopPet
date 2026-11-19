"""Validate only changed staged resources, then install with a hash-checked backup."""
from pathlib import Path
import json,hashlib,shutil,os
from glb import load,read_accessor

stage=Path(os.environ.get('BA_FX_INSTALL_STAGE','.assets/fx037-stage'));base=Path('characters');backup=Path(os.environ.get('BA_FX_INSTALL_BACKUP','.assets/pre037'));changes=[]
suffix=os.environ.get('BA_FX_INSTALL_SUFFIX','037')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def geometry(d,b,n):
 return [{**{k:read_accessor(d,b,v) for k,v in p['attributes'].items()},'indices':read_accessor(d,b,p['indices']) if 'indices' in p else None} for p in d['meshes'][n['mesh']]['primitives']]
def texture_refs(v):
 if not isinstance(v,dict):return
 for k,x in v.items():
  if k.endswith(('Texture','Tex')) and isinstance(x,dict) and 'index' in x:yield x['index']
  else:yield from texture_refs(x)
for p in sorted(stage.glob('*/*')):
 if not p.is_file():continue
 rel=p.relative_to(stage);old=base/rel
 assert old.exists(),rel
 if sha(p)==sha(old):continue
 row={'path':str(rel),'old':sha(old),'new':sha(p)}
 if p.suffix=='.glb':
  d,b=load(p);o,ob=load(old);names={n.get('name'):n for n in d['nodes']};count=0
  for n in o['nodes']:
   if 'mesh' not in n or n.get('name','').startswith(('cafe_fx_','cafe_particle_')):continue
   assert geometry(o,ob,n)==geometry(d,b,names[n['name']]),(rel,n['name'],'base geometry changed');count+=1
  row['unchangedBaseMeshes']=count
  for m in d['materials']:
   for t in texture_refs(m):assert 0<=t<len(d.get('textures',[])),(rel,'texture',t)
  for a in d.get('animations',[]):
   for ch in a['channels']:
    assert ch['target']['node']<len(d['nodes']);s=a['samplers'][ch['sampler']];t=read_accessor(d,b,s['input']);assert t==sorted(t);assert len(t)*(3 if s.get('interpolation')=='CUBICSPLINE' else 1)==len(read_accessor(d,b,s['output']))
  for v in d['bufferViews']:assert v.get('byteOffset',0)+v['byteLength']<=len(b)
  assert not any(v.get('uri') for key in ['buffers','images'] for v in d.get(key,[]))
 elif p.suffix=='.json':
  o=json.loads(old.read_text('utf8'));d=json.loads(p.read_text('utf8'));angles=[]
  for before,after in zip(o['furniture'],d['furniture']):
   if before.get('yaw')!=after.get('yaw'):angles.append([after['id'],before.get('yaw'),after.get('yaw')]);before['yaw']=after['yaw']
  assert o==d,(rel,'unexpected manifest change');row['angles']=angles
 else:raise ValueError(rel)
 changes.append(row)
Path(f'test-results/stage{suffix}-verification.json').write_text(json.dumps(changes,indent=2),'utf8')
for row in changes:
 rel=Path(row['path']);old=base/rel;dest=backup/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():assert sha(dest)==row['old'],(rel,'backup differs')
 else:shutil.copyfile(old,dest)
 assert sha(old)==row['old'];shutil.copyfile(stage/rel,old);assert sha(old)==row['new']
Path(f'test-results/resources{suffix}-installed.json').write_text(json.dumps(changes,indent=2),'utf8');print('Validated and installed',len(changes),'files')
