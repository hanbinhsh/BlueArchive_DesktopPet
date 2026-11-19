"""Compare Ichika eye channels and events with the original export, read-only."""
from pathlib import Path
import json,hashlib
from glb import load,read_accessor
R=Path(__file__).resolve().parents[1];T=R/'test-results'
read=lambda p:json.loads(p.read_text('utf8'));index=read(T/'action-source-index.json');rows=[]
for key in ['ichika','ichika_swimsuit']:
 cp=R/'characters'/key/'character.json';c=read(cp);d,b=load(cp.parent/'model.glb');sources=[]
 for entry in index[key]:
  sd,sb=load(R/entry['path']);sources.append((sd,sb))
 clips=[]
 for action in c['actions']:
  a=next(a for a in d['animations']if a['name']==action['clip']);sd,sb=next((sd,sb)for sd,sb in sources if any(x['name']==a['name']for x in sd.get('animations',[])))
  original=next(x for x in sd['animations']if x['name']==a['name']);count=0
  for x,y in zip(a['channels'],original['channels']):
   name=d['nodes'][x['target']['node']]['name']
   if not any(term in name.lower()for term in ['eye','brow','blow']):continue
   assert name==sd['nodes'][y['target']['node']]['name']and x['target']['path']==y['target']['path']
   p=a['samplers'][x['sampler']];q=original['samplers'][y['sampler']];assert p.get('interpolation')==q.get('interpolation')
   for prop in ['input','output']:assert read_accessor(d,b,p[prop])==read_accessor(sd,sb,q[prop]),(key,action['id'],name)
   count+=1
  extras=d['scenes'][0]['extras'];native=sd['scenes'][0]['extras'];meta=next(x for x in extras['BAAD_unity_animation']['clips']if x['track']==a['name']);sm=next(x for x in native['BAAD_unity_animation']['clips']if x['track']==a['name']);assert meta==sm
  clips.append(dict(action=action['id'],clip=a['name'],eyeAndBrowChannels=count,sourceMetadataEqual=True))
 rows.append(dict(character=key,actions=clips,modelSha256=hashlib.sha256((cp.parent/'model.glb').read_bytes()).hexdigest()))
report=dict(complete=True,source='Original JP r96 exported curves and Unity events',characters=rows,matchedEyeAndBrowChannels=sum(x['eyeAndBrowChannels']for row in rows for x in row['actions']))
(T/'ichika041-source.json').write_text(json.dumps(report,indent=2),'utf8');print('Verified original eye/brow channels:',report['matchedEyeAndBrowChannels'])
