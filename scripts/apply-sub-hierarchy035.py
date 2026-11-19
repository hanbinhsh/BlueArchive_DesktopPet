"""Fix clone reparenting without rebuilding unrelated geometry or shader patches."""
import pathlib,json,copy,shutil,re,sys
from glb import load,save
from fx_hierarchy import annotate,reparent
source=json.loads(pathlib.Path('.assets/cafe-fx-all033/source.json').read_text('utf8'));root=pathlib.Path(sys.argv[1]);report=[]
def walk(n):
 yield n
 for c in n['children']:yield from walk(c)
for effect in source['effects'].values():annotate(effect)
paths={n['path']:n for effect in source['effects'].values() for n in walk(effect)}
ids={n['particleId']:n for effect in source['effects'].values() for n in walk(effect) if n.get('particleId')}
for cp in pathlib.Path('characters').glob('*/character.json'):
 for filename in {f['model'] for f in json.loads(cp.read_text('utf8')).get('furniture',[])}:
  target=root/cp.parent.name/filename;p=target if target.exists() else cp.parent/filename;d,b=load(p);changed=[]
  particles={m['name']:m.get('extras',{}).get('BA_cafeParticle') for m in d['materials']}
  for n in d['nodes']:
   spawn=n.get('extras',{}).get('BA_subEmitter')
   if not spawn:continue
   spec=particles.get(spawn['parent']);parent=paths[spec['sourceName']]
   candidates=[ids[s['target']] for s in parent['subEmitters'] if n['name'].endswith('_'+ids[s['target']]['name'])]
   if len(candidates)!=1:raise ValueError((p,n['name'],len(candidates)))
   child=copy.deepcopy(candidates[0]);reparent(child,parent);q=child['rotation'];rotation=[q[0],-q[1],-q[2],q[3]]
   if any(abs(a-b)>1e-6 for a,b in zip(n.get('rotation',[0,0,0,1]),rotation)) or any(abs(a-b)>1e-6 for a,b in zip(n.get('scale',[1,1,1]),child['scale'])):
    n['rotation']=rotation;n['scale']=child['scale'];changed.append(n['name'])
  if changed:
   if not target.parent.exists():shutil.copytree(cp.parent,target.parent)
   save(target,d,b);report.append({'character':cp.parent.name,'file':filename,'nodes':changed})
pathlib.Path('test-results/subhierarchy035-applied.json').write_text(json.dumps(report,indent=2),'utf8');print('updated',len(report),'models',sum(len(r['nodes']) for r in report),'cloned emitters')
