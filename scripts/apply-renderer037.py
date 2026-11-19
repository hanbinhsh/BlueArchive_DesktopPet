"""Preserve disabled particle renderers while retaining their event simulation."""
from pathlib import Path
from collections import defaultdict
import json,shutil
from glb import load,save

flags=defaultdict(set)
def walk(n):
    if n.get('renderer') and 'm_Enabled' in n['renderer']:
        flags[n['path']].add(bool(n['renderer']['m_Enabled']))
    for c in n['children']:walk(c)
for folder in ['cafe-fx-all033','cafe-fx-nested035','cafe-fx036','cafe-phone036']:
    d=json.loads((Path('.assets')/folder/'source.json').read_text('utf8'))
    for effect in d['effects'].values():walk(effect)
    del d
root=Path('.assets/fx037-stage');report=[]
for p in Path('characters').glob('*/f*.glb'):
    d,b=load(p);changes=[]
    for m in d['materials']:
        s=m.get('extras',{}).get('BA_cafeParticle')
        if not s:continue
        values=flags.get(s['sourceName'],set())
        if values=={False}:
            s['renderer']['m_Enabled']=False;changes.append(s['sourceName'])
        elif len(values)>1:raise ValueError('Ambiguous renderer flag: '+s['sourceName'])
    if changes:
        target=root/p.relative_to('characters')
        if not target.parent.exists():shutil.copytree(p.parent,target.parent)
        save(target,d,b);report.append({'path':str(p.relative_to('characters')),'particles':len(changes),'sources':sorted(set(changes))})
Path('test-results/renderers037-applied.json').write_text(json.dumps(report,indent=2),'utf8')
print('Restored hidden renderers in',len(report),'models',sum(r['particles'] for r in report),'particles')
