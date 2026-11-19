"""Restore original group billboard components into converted effect hierarchies."""
import pathlib,json,re,sys
from glb import load,save
rows=json.loads(pathlib.Path('.assets/fx-billboards035.json').read_text('utf8'));specs={r['path']:r for r in rows};report=[]
for p in pathlib.Path(sys.argv[1]).glob('*/f*.glb'):
 d,b=load(p);parents={c:i for i,n in enumerate(d['nodes']) for c in n.get('children',[])};changed=[]
 def path(i):
  name=d['nodes'][i].get('name','');match=re.fullmatch(r'cafe_fx_\d+_(.+)',name)
  if not match:return ''
  return (path(parents[i]) if i in parents else '')+'/'+match[1]
 for i,n in enumerate(d['nodes']):
  key=path(i)
  if key in specs:n.setdefault('extras',{})['BA_fxBillboard']={'fixedY':specs[key]['fixedY']};changed.append(key)
 if changed:save(p,d,b);report.append({'file':str(p),'groups':changed})
pathlib.Path('test-results/billboards035-applied.json').write_text(json.dumps(report,indent=2),'utf8');print('Models',len(report),'groups',sum(len(r['groups']) for r in report))
