"""Apply original ActivationTracks, including idle-only objects hidden during interactions."""
import json,pathlib,sys,re,copy
from glb import load,save,compact
root=pathlib.Path(sys.argv[1]);source=json.loads(pathlib.Path('test-results/activation035-source.json').read_text());report=[]
for cp in root.glob('*/character.json'):
 if sys.argv[2:] and cp.parent.name not in sys.argv[2:]:continue
 for f in json.loads(cp.read_text('utf8')).get('furniture',[]):
  path=cp.parent/f['model'];d,b=load(path);e=d['scenes'][0].get('extras',{}).get('BA_furniture',{});icon=f.get('sourceTimeline',e.get('sourceTimeline'));group=f.get('sourceGroup',e.get('group'));rows=[r for r in source if r['icon']==icon and r['binding'] and not r['muted']]
  if not rows:continue
  vis=d['scenes'][0].setdefault('extras',{}).setdefault('BA_pet_visibility',{'defaults':{},'clips':{}});events=vis['clips'].setdefault(f['clip'],[]);changes=[]
  for name in {r['binding'] for r in rows}:
   matches=[i for i,n in enumerate(d['nodes']) if re.sub(r'^furniture_\d+_','',n.get('name',''))==name]
   if not matches:continue
   spans=[(r['start'],r['start']+r['duration']) for r in rows if r['binding']==name and r['path'][0]==group];times=sorted({0.,f['duration'],*[v for span in spans for v in span]});keys=[]
   for t in times:
    active=any(a<=t<z for a,z in spans)
    if not keys or keys[-1][1]!=active:keys.append([t,active])
   for ix in matches:
    events[:]=[v for v in events if v['node']!=ix];events.append({'node':ix,'keys':keys});vis['defaults'][str(ix)]=keys[0][1];changes.append([name,keys])
  # An authored static liquid uses the same DSFX material as its animated copy.
  if cp.parent.name=='kokona':
   name='FX_MAT_cafe_01_b_table_Water_01';template=next(m for m in d['materials'] if m.get('extras',{}).get('BA_cafeParticle',{}).get('material',{}).get('name')==name)
   for m in d['materials']:
    if m.get('name')==name:
     m.clear();m.update(copy.deepcopy(template));m['name']=name;m['extras'].pop('BA_cafeParticle');m['pbrMetallicRoughness']['baseColorFactor']=[1,1,1,1]
  if changes:save(path,d,compact(d,b));report.append({'character':cp.parent.name,'id':f['id'],'changes':changes})
pathlib.Path('test-results/activation035-applied.json').write_text(json.dumps(report,indent=2),'utf8');print('updated',len(report))
