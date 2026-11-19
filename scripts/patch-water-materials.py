"""Update only verified water materials, preserving the baked motion/geometry."""
import json,pathlib,sys,shutil,os
import UnityPy
from glb import load,save,compact
from furniture_water_fx import adapt_water_fx
from source_dependencies import resolve_cached

root=pathlib.Path(os.environ.get('BA_CHARACTER_OUTPUT','.assets/pending-repairs'))
files=[str(p) for p in pathlib.Path('.assets/selected').glob('*.bundle') if 'icepool' in p.name]
env=UnityPy.load(*files)
materials={o.read().m_Name:o.read() for o in env.objects if o.type.name=='Material' and o.read().m_Name.startswith('FX_MAT_Cafe_Icepool_')}
character='eimi_swimsuit';target=root/character
if not target.exists():shutil.copytree(pathlib.Path('characters')/character,target)
report=[]
manifest=json.loads((target/'character.json').read_text('utf8'))
for name in set(f['model'] for f in manifest['furniture']):
    p=target/name;doc,binary=load(p)
    for mat in doc['materials']:
        source=materials.get(mat['name'])
        if source and resolve_cached(env,lambda:adapt_water_fx(source,mat,doc,binary)):report.append(mat['name'])
    save(p,doc,compact(doc,binary))
pathlib.Path('test-results/water-material-repair.json').write_text(json.dumps(report,indent=2))
print('Updated',report,flush=True)
