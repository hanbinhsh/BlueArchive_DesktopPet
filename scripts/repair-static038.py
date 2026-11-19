"""Restore authored static DSFX layers from original materials, without mesh edits."""
from pathlib import Path
import json,sys,shutil,UnityPy
from glb import load,save,compact
from furniture_water_fx import adapt_water_fx
from source_dependencies import resolve_cached
from furniture_tint import adapt_simple_tint

env=UnityPy.load(*map(str,Path('.assets/selected').glob('*cafe*materials*.bundle')))
originals={o.read().m_Name:o.read()for o in list(env.objects)if o.type.name=='Material'}
stage=Path('.assets/repair038-stage');report=[]
for character,file in [('tsurugi_swimsuit','f4302_0.glb'),('hina_swimsuit','f4301_0.glb'),('mine','f207310_0.glb')]:
 target=stage/character
 if not target.exists():shutil.copytree(Path('characters')/character,target)
 d,b=load(Path('characters')/character/file);changes=[]
 for m in d['materials']:
  if m.get('extras',{}).get('BA_cafeParticle'):continue
  if m.get('extras',{}).get('BA_poolWater'):
   m['extras'].update(BA_sourceRenderQueue=3000,BA_renderOrder=3000000000);changes.append(m['name']+' render queue');continue
  if m.get('extras',{}).get('BA_waterFx') or m.get('extras',{}).get('BA_smokeFx'):continue
  original=originals.get(m.get('name'))
  if original is None:continue
  if resolve_cached(env,lambda:adapt_water_fx(original,m,d,b)):changes.append(m['name'])
  if m['name']=='FX_MAT_my_event14_table_Tea' and resolve_cached(env,lambda:adapt_simple_tint(original,m)):changes.append(m['name'])
 save(target/file,d,compact(d,b));report.append(dict(character=character,file=file,materials=changes))
Path('test-results/static038-repairs.json').write_text(json.dumps(report,indent=2),'utf8');print(report)
