"""Prove the repair only adds original phone FX and preserves the scene."""
from pathlib import Path
import json,hashlib
from glb import load,read_accessor
R=Path(__file__).resolve().parents[1];T=R/'test-results'
read=lambda p:json.loads(p.read_text('utf8'))
before=R/'release/v0.2.19/win-unpacked/resources/characters/ichika/f10206_0.glb';after=R/'.assets/phone042/ichika/f10206_0.glb'
old,ob=load(before);new,nb=load(after)
assert old['scenes']==new['scenes']and old['skins']==new['skins']
assert len(new['nodes'])>len(old['nodes'])and len(new['meshes'])>len(old['meshes'])
parent=next(i for i,n in enumerate(old['nodes'])if n.get('name')=='FX_my_autumnsports_01_chair_03_Phone_Emo_01')
for i,n in enumerate(old['nodes']):
 a=dict(n);b=dict(new['nodes'][i])
 if i==parent:
  a.pop('children',None);b.pop('children',None)
  assert new['nodes'][i]['children'][:len(n['children'])]==n['children']
 assert a==b,(i,n.get('name'))
assert len(old['animations'])==len(new['animations'])==1
channels=0
for a,b in zip(old['animations'],new['animations']):
 assert a['channels']==b['channels']and a['name']==b['name']
 for x,y in zip(a['samplers'],b['samplers']):
  assert x.get('interpolation')==y.get('interpolation')
  for prop in ['input','output']:assert read_accessor(old,ob,x[prop])==read_accessor(new,nb,y[prop])
 channels+=len(a['channels'])
for x,y in zip(old['meshes'],new['meshes']):
 assert len(x['primitives'])==len(y['primitives'])
 for p,q in zip(x['primitives'],y['primitives']):
  assert p['material']==q['material']and p['attributes'].keys()==q['attributes'].keys()
  for k in p['attributes']:assert read_accessor(old,ob,p['attributes'][k])==read_accessor(new,nb,q['attributes'][k])
  assert read_accessor(old,ob,p['indices'])==read_accessor(new,nb,q['indices'])
newfx=[m for m in new['materials'][len(old['materials']):]if m.get('extras',{}).get('BA_cafeParticle')]
assert len(newfx)==30 and all('Phone_Emo_01/'in m['extras']['BA_cafeParticle']['sourceName']for m in newfx)
for m in newfx:
 spec=m['extras']['BA_cafeParticle'];control=spec['control'];assert abs(control['start']-.033333335)<1e-9 and control['binding']==old['nodes'][parent]['name']
 assert abs(control['duration']+control['start']-17.3)<1e-9
 if spec['sourceName'].endswith(('Phone_Chat','Phone_Chat_1','Phone_Chat_2')):
  assert m['doubleSided']==(spec['material']['floats']['_Cull_Mode']==0)
source=read(R/'.assets/cafe-embedded042/source.json');assert not source['errors']
assert all(not r['omitted']for r in read(T/'ichika042-phone-adaptation.json'))
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
report=dict(complete=True,changedResource='ichika/f10206_0.glb',beforeSha256=sha(before),afterSha256=sha(after),unchangedAnimationChannels=channels,unchangedOldMeshes=len(old['meshes']),addedOriginalParticles=30,originalVisibilityAndMouthEventsUnchanged=True,nativeActivationStart=.033333335,sourceErrors=[])
(T/'ichika042-resource-proof.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps(report,indent=2))
