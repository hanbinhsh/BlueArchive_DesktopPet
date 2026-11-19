"""Restore omitted Timeline override tracks from the cached original clips."""
import json,pathlib,sys,shutil,re,zlib,collections,math
from glb import load,save,append_accessor,compact
from unity_recorded import curves,sample,euler_quaternion
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '.assets/fx035-stage');wanted=set(sys.argv[2:]);source=json.loads(pathlib.Path('test-results/infinite035-source.json').read_text());report=[]
for cp in pathlib.Path('characters').glob('*/character.json'):
 if wanted and cp.parent.name not in wanted:continue
 for f in json.loads(cp.read_text('utf8')).get('furniture',[]):
  target=root/cp.parent.name/f['model'];base=target if target.exists() else cp.parent/f['model'];d,b=load(base);extra=d['scenes'][0].get('extras',{}).get('BA_furniture',{});icon=f.get('sourceTimeline',extra.get('sourceTimeline'));group=f.get('sourceGroup',extra.get('group'));tracks=[r for r in source if r['icon']==icon and r['path'][0]==group]
  if not tracks:continue
  parent={c:i for i,n in enumerate(d['nodes']) for c in n.get('children',[])};hashes=collections.defaultdict(set)
  for ix,n in enumerate(d['nodes']):
   if n.get('name','').startswith('cafe_fx_'):continue
   chain=[];i=ix
   while True:
    chain.insert(0,re.sub(r'^(?:furniture_\d+_|partner_\d+_)','',d['nodes'][i].get('name','')));hashes[zlib.crc32('/'.join(chain).encode())].add(ix)
    if i not in parent:break
    i=parent[i]
  changed=[]
  for track in tracks:
   clip=track['clip'];cs=curves(clip);cursor=0
   for binding in clip['m_ClipBindingConstant']['genericBindings']:
    kind,attr=binding['typeID'],binding['attribute'];width=(4 if attr==2 else 3) if kind==4 else 1;indices=list(range(cursor,cursor+width));cursor+=width
    if kind!=4 and not(kind==1 and attr==2086281974):continue
    candidates=list(hashes.get(binding['path'],[]));plain=[i for i in candidates if 'mesh' not in d['nodes'][i]]
    if len(plain)==1:candidates=plain
    if len(candidates)!=1:report.append({'character':cp.parent.name,'id':f['id'],'unresolved':binding,'nodes':candidates});continue
    node=candidates[0];times=sorted({0.,f['duration'],*[min(f['duration'],i/30) for i in range(math.ceil(f['duration']*30)+1)],*[t for ix in indices for t,_ in cs[ix] if 0<=t<=f['duration']]});values=[[sample(cs[ix],t) for ix in indices] for t in times]
    if kind==1:
     vis=d['scenes'][0].setdefault('extras',{}).setdefault('BA_pet_visibility',{'defaults':{},'clips':{}});events=vis['clips'].setdefault(f['clip'],[]);events[:]=[e for e in events if e['node']!=node];keys=[]
     for t,v in zip(times,values):
      state=v[0]>=.5
      if not keys or keys[-1][1]!=state:keys.append([t,state])
     events.append({'node':node,'keys':keys});vis['defaults'][str(node)]=keys[0][1]
    else:
     prop={1:'translation',2:'rotation',3:'scale',4:'rotation'}[attr]
     if attr==1:values=[[-v[0],v[1],v[2]] for v in values]
     elif attr==2:values=[[v[0],-v[1],-v[2],v[3]] for v in values]
     elif attr==4:values=[euler_quaternion(v) for v in values]
     for a in d['animations']:
      if a['name']!=f['clip']:continue
      a['channels']=[ch for ch in a['channels'] if ch['target']!={'node':node,'path':prop}];si=len(a['samplers']);a['samplers'].append({'input':append_accessor(d,b,[[t] for t in times],'SCALAR'),'output':append_accessor(d,b,values,'VEC4' if prop=='rotation' else 'VEC3'),'interpolation':'LINEAR'});a['channels'].append({'sampler':si,'target':{'node':node,'path':prop}})
    changed.append([d['nodes'][node]['name'],kind,attr])
  if changed:
   target.parent.mkdir(parents=True,exist_ok=True)
   if not (target.parent/'character.json').exists():shutil.copyfile(cp,target.parent/'character.json')
   save(target,d,compact(d,b));report.append({'character':cp.parent.name,'id':f['id'],'changed':changed})
pathlib.Path('test-results/infinite035-applied.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps(report,indent=2))
