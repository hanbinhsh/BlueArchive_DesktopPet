"""Bake nested FX Timeline transforms and preserve animated material parameters."""
import json,pathlib,re,zlib,math,sys
from glb import load,save,compact,append_accessor
from unity_recorded import curves,sample,euler_quaternion
root=pathlib.Path(sys.argv[1]);source=json.loads(pathlib.Path('.assets/cafe-fx-nested035/source.json').read_text());effect=next(iter(source['effects'].values()));p=root/'eimi_swimsuit/f210327_0.glb';d,b=load(p);f=json.loads((p.parent/'character.json').read_text('utf8'))['furniture'][0];nodes={};materials={}
def walk(n):
 yield n
 for c in n['children']:yield from walk(c)
def link(n,parent=None):
 names=[i for i,x in enumerate(d['nodes']) if re.fullmatch(r'cafe_fx_\d+_'+re.escape(n['name']),x.get('name','')) and (parent is None or i in d['nodes'][parent].get('children',[]))]
 if len(names)!=1:raise ValueError((n['path'],names))
 ix=names[0];nodes[n['path']]=ix
 materials[n['path']]=[d['meshes'][d['nodes'][c]['mesh']]['primitives'][0]['material'] for c in d['nodes'][ix].get('children',[]) if d['nodes'][c].get('extras',{}).get('BA_cafeParticle')]
 for c in n['children']:link(c,ix)
link(effect)
report=[]
for track in effect['animationTracks']:
 binding=next(n for n in walk(effect) if n['name']==track['binding']);paths={zlib.crc32(n['path'][len(binding['path'])+1:].encode()):n for n in walk(binding) if n is not binding};paths[0]=binding
 cs=curves(track['clip']);cursor=0
 for binding_data in track['clip']['m_ClipBindingConstant']['genericBindings']:
  kind,attr=binding_data['typeID'],binding_data['attribute'];width=(4 if attr==2 else 3) if kind==4 else 1;indices=list(range(cursor,cursor+width));cursor+=width;n=paths[binding_data['path']];ix=nodes[n['path']]
  times=sorted({0.,f['duration'],*[min(f['duration'],i/30) for i in range(math.ceil(f['duration']*30)+1)],*[t for i in indices for t,_ in cs[i] if 0<=t<=f['duration']]});values=[[sample(cs[i],t) for i in indices] for t in times]
  if kind==4:
   prop={1:'translation',2:'rotation',3:'scale',4:'rotation'}[attr]
   if attr==1:values=[[-v[0],v[1],v[2]] for v in values]
   elif attr==2:values=[[v[0],-v[1],-v[2],v[3]] for v in values]
   elif attr==4:values=[euler_quaternion(v) for v in values]
   a=next(a for a in d['animations'] if a['name']==f['clip']);a['channels']=[ch for ch in a['channels'] if ch['target']!={'node':ix,'path':prop}];si=len(a['samplers']);a['samplers'].append({'input':append_accessor(d,b,[[t] for t in times],'SCALAR'),'output':append_accessor(d,b,values,'VEC4' if prop=='rotation' else 'VEC3'),'interpolation':'LINEAR'});a['channels'].append({'sampler':si,'target':{'node':ix,'path':prop}})
  elif kind in [23,199] and binding_data['customType']==22:
   high=attr>>28;category='floats' if high==8 else 'colors';component=None if high==8 else high-4
   keys={k for m in n.get('materials',[]) for k in m[category] if zlib.crc32(k.encode())&0xfffffff==attr&0xfffffff}
   if len(keys)!=1 or component is not None and component not in range(4):raise ValueError(binding_data)
   prop=next(iter(keys))
   for mi in materials[n['path']]:d['materials'][mi]['extras']['BA_cafeParticle'].setdefault('propertyTracks',[]).append({'category':category,'property':prop,'component':component,'times':times,'values':[v[0] for v in values]})
  else:raise ValueError(binding_data)
  report.append([n['path'],kind,prop])
save(p,d,compact(d,b));pathlib.Path('test-results/nested035-applied.json').write_text(json.dumps(report,indent=2),'utf8');print('restored nested curves',len(report))
