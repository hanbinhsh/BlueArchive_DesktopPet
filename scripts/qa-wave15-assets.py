"""Verify new original curves and packed skin, and lock the previous resources."""
import json,hashlib,sys,math
from pathlib import Path
import UnityPy
from UnityPy.helpers.MeshHelper import MeshHandler,unpack_ints
from compressed_skin import decode_packed_skin
from glb import load,read_accessor
R=Path(__file__).resolve().parents[1];T=R/'test-results';stage=R/'.assets/wave15-final'
read=lambda p:json.loads(p.read_text('utf8'))
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
profiles=read(R/'scripts/wave15-profiles.json');specs=read(R/'scripts/roster-wave15.json');index=read(T/'action-source-index.json');rows=[]
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
 assert d['scenes'][0]['extras'].get('BA_halo_follow')or profiles[key].get('noHalo')
 assert any('halo'in n.get('name','').lower()and'mesh'in n for n in d['nodes'])or profiles[key].get('noHalo')
 assert not any(x.get('uri')for x in d.get('buffers',[])+d.get('images',[]))
 assert (stage/key/'thumbnail.png').is_file();assert c.get('mouth')or profiles[key].get('noMouthAtlas')
 for f in c.get('furniture',[]):
  fd,fb=load(stage/key/f['model']);assert any(a['name']==f['clip']for a in fd['animations']);assert f['duration']>0
  assert not any(x.get('uri')for x in fd.get('buffers',[])+fd.get('images',[]))
 rows.append(dict(character=key,actions=len(c['actions']),furniture=len(c.get('furniture',[])),unchangedAuthoredChannels=curves,modelSha256=sha(stage/key/'model.glb')))
previous=read(T/'release042-resources.json')
for item in previous:assert sha(R/'characters'/item['path'])==item['sha256'],item['path']
framing=[r for r in read(T/'expanded-framing.json')if r['character']in specs]
(T/'wave15-framing.json').write_text(json.dumps(framing,indent=2),'utf8')
report=dict(added=rows,baseVersion='0.2.20',unchangedPreviousFiles=len(previous))
(T/'wave15-resources.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps(report,indent=2))
