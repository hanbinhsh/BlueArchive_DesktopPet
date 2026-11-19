"""Bake the original mini-game director transforms using object identities."""
import json,math,re,zlib
from pathlib import Path
from glb import load,save,compact,append_accessor
from unity_recorded import curves,sample,euler_quaternion

source=json.loads(Path('.assets/cafe-blocks037/source.json').read_text('utf8'))
root=Path('.assets/blocks037-stage');report=[]
def walk(n):
 yield n
 for c in n['children']:yield from walk(c)
for cp in root.glob('*/character.json'):
 for f in json.loads(cp.read_text('utf8'))['furniture']:
  p=cp.parent/f['model'];d,b=load(p);changes=[]
  metadata=d['scenes'][0].get('extras',{}).get('BA_furniture',{})
  if f.get('sourceTimeline',metadata.get('sourceTimeline'))!='my_event088_gamingspace':continue
  timeline=next(t for t in source['timelines']if t['icon']=='my_event088_gamingspace')
  group=f.get('sourceGroup',metadata.get('group'));controls=[c for c in timeline['controls']if c['parents'] and c['parents'][0]==group and 'Block_Extra'in c['prefab']]
  for control in controls:
   effect=source['effects'][control['prefab']]
   for track in effect.get('animationTracks',[]):
    bindings=[n for n in walk(effect)if n['name']==track['binding']];assert len(bindings)==1,(track['binding'],len(bindings))
    binding=bindings[0];paths={zlib.crc32(n['path'][len(binding['path'])+1:].encode()):[] for n in walk(binding)};paths[0]=[binding]
    for n in walk(binding):
     if n is not binding:paths[zlib.crc32(n['path'][len(binding['path'])+1:].encode())].append(n)
    cs=curves(track['clip']);cursor=0
    for bind in track['clip']['m_ClipBindingConstant']['genericBindings']:
     kind,attr=bind['typeID'],bind['attribute'];width=(4 if attr==2 else 3)if kind==4 else 1;indices=list(range(cursor,cursor+width));cursor+=width
     targets=paths[bind['path']]
     assert kind==4,(kind,attr)
     times=[min(f['duration'],i/30)for i in range(math.ceil(f['duration']*30)+1)]
     values=[[sample(cs[ix],((t-control['start'])*control['speed']+control['clipIn']-track['start'])*track['speed']+track['clipIn'])for ix in indices]for t in times]
     prop={1:'translation',2:'rotation',3:'scale',4:'rotation'}[attr]
     if attr==1:values=[[-v[0],v[1],v[2]]for v in values]
     elif attr==2:values=[[v[0],-v[1],-v[2],v[3]]for v in values]
     elif attr==4:values=[euler_quaternion(v)for v in values]
     ids={n['objectId']for n in targets};nodes=[i for i,n in enumerate(d['nodes'])if n.get('extras',{}).get('BA_sourceObjectId')in ids]
     assert nodes,(control['prefab'],track['binding'],bind['path'])
     a=next(a for a in d['animations']if a['name']==f['clip'])
     a['channels']=[ch for ch in a['channels']if not(ch['target']['node']in nodes and ch['target']['path']==prop)]
     si=len(a['samplers']);a['samplers'].append({'input':append_accessor(d,b,[[t]for t in times],'SCALAR'),'output':append_accessor(d,b,values,'VEC4'if prop=='rotation'else'VEC3'),'interpolation':'LINEAR'})
     for ix in nodes:a['channels'].append({'sampler':si,'target':{'node':ix,'path':prop}})
     changes.append({'root':control['prefab'],'binding':track['binding'],'pathHash':bind['path'],'property':prop,'nodes':nodes})
  save(p,d,compact(d,b));report.append({'character':cp.parent.name,'id':f['id'],'curves':changes})
Path('test-results/blocks037-curves.json').write_text(json.dumps(report,indent=2),'utf8');print('Nested mini-game models',len(report),'curves',sum(len(r['curves'])for r in report))
