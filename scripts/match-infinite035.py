import json,pathlib,sys,re,zlib,collections
sys.path.insert(0,'scripts');from glb import load
rs=json.loads(pathlib.Path('test-results/infinite035-source.json').read_text());report=[]
for cp in pathlib.Path('characters').glob('*/character.json'):
 for f in json.loads(cp.read_text('utf8')).get('furniture',[]):
  d,b=load(cp.parent/f['model']);e=d['scenes'][0].get('extras',{}).get('BA_furniture',{});icon=f.get('sourceTimeline',e.get('sourceTimeline'));group=f.get('sourceGroup',e.get('group'));selected=[r for r in rs if r['icon']==icon and r['path'][0]==group]
  if not selected:continue
  parent={c:i for i,n in enumerate(d['nodes']) for c in n.get('children',[])};hashes=collections.defaultdict(set)
  for ix,n in enumerate(d['nodes']):
   if n.get('name','').startswith('cafe_fx_'):continue
   chain=[];i=ix
   while True:
    chain.insert(0,re.sub(r'^furniture_\d+_','',d['nodes'][i].get('name','')));hashes[zlib.crc32('/'.join(chain).encode())].add(ix)
    if i not in parent:break
    i=parent[i]
  for r in selected:
   for bind in r['clip']['m_ClipBindingConstant']['genericBindings']:
    found=[(i,d['nodes'][i].get('name'), 'mesh'in d['nodes'][i]) for i in hashes.get(bind['path'],[])];report.append({'character':cp.parent.name,'furniture':f['id'],'track':r['path'],'binding':bind,'nodes':found})
pathlib.Path('test-results/infinite035-matches.json').write_text(json.dumps(report,indent=2),'utf8')
for r in report:
 if r['character'] in ['hoshino_battle','eimi_swimsuit','hina_swimsuit','momoi','midori','mine','kikyou_swimsuit']:print(r['character'],r['track'][-1],r['binding']['typeID'],r['binding']['attribute'],r['nodes'])
print('total',len(report),'unmatched',sum(not r['nodes'] for r in report))
