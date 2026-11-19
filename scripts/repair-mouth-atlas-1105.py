"""Repair confirmed legacy Hina 8x8 metadata against original 4x4 materials.

The baked geometry already uses the correct original 0,.75 base UV. Only the
grid metadata and reset-event tile were wrong; other authored events stay intact.
"""
import pathlib,json,shutil
from glb import load,save
root=pathlib.Path('characters');backup=pathlib.Path('.assets/pre-029');report=[]
materials={'Hina_Original_Mouth','CH0063_Mouth'}
def fix(spec):
 if spec.get('material') not in materials:return False
 changed=spec.get('columns')!=4 or spec.get('rows')!=4 or spec['defaultTile']!=300
 spec.update(columns=4,rows=4,defaultTile=300)
 for events in spec.get('events',{}).values():
  for e in events:
   if e['tile']==600:e['tile']=300;changed=True
 return changed
def keep(p):
 b=backup/p.relative_to(root);b.parent.mkdir(parents=True,exist_ok=True)
 if not b.exists():shutil.copyfile(p,b)
for p in root.glob('*/character.json'):
 c=json.loads(p.read_text('utf8'));changed=fix(c.get('mouth',{}))
 if c.get('mouth',{}).get('material') in materials:
  for f in c.get('furniture',[]):
   for e in f.get('mouthEvents',[]):
    if e['tile']==600:e['tile']=300;changed=True
 if changed:keep(p);p.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n','utf8');report.append(str(p))
 for model in {c['model'],*(f['model'] for f in c.get('furniture',[]))}:
  p2=p.parent/model;d,b=load(p2);changed=False
  for scene in d.get('scenes',[]):
   for spec in scene.get('extras',{}).get('BA_furniture_mouths',[]):changed=fix(spec) or changed
  if changed:keep(p2);save(p2,d,b);report.append(str(p2))
pathlib.Path('test-results/mouth-repairs-1105.json').write_text(json.dumps(report,indent=2));print(report)
