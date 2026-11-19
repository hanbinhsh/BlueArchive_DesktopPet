"""Audit all installed float color attributes without altering assets."""
from pathlib import Path
import json, struct, math
from glb import load,read_accessor
rows=[]
for manifest in Path('characters').glob('*/character.json'):
 c=json.loads(manifest.read_text('utf8'))
 for name in {c['model'],*[f['model'] for f in c.get('furniture',[])]}:
  d,b=load(manifest.parent/name);issues=[];seen=set()
  for mesh in d.get('meshes',[]):
   for primitive in mesh['primitives']:
    idx=primitive['attributes'].get('COLOR_0')
    if idx is None or idx in seen:continue
    seen.add(idx);a=d['accessors'][idx]
    if a['componentType']!=5126:continue
    vals=read_accessor(d,b,idx)
    if any(not math.isfinite(x) or x<0 or x>1 for v in vals for x in v):issues.append({'accessor':idx,'max':max(x for v in vals for x in v)})
  rows.append({'character':c['id'],'model':name,'issues':issues})
Path('test-results/model-material-audit-1105.json').write_text(json.dumps(rows,indent=2))
print(json.dumps({'scanned':len(rows),'affected':[r for r in rows if r['issues']]},indent=2))
