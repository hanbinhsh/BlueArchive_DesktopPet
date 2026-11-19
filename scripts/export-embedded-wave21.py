"""Export audited native character-embedded AND persistent furniture FX roots for Wave 21."""
from pathlib import Path
import os, sys, json, runpy

W = Path('.assets')
T = Path('test-results')
out = W / 'cafe-embedded21'
out.mkdir(exist_ok=True)
audit = json.loads((T / 'wave21-embedded-audit.json').read_text('utf8'))
specs = json.loads(Path('scripts/roster-wave21.json').read_text('utf8'))
icons = sorted({r['icon'] for r in audit['missing']})
if not icons:
    (out / 'source.json').write_text(json.dumps(dict(timelines=[], effects={}, errors=[])), 'utf8')
    print('No missing embedded/persistent FX roots.')
    sys.exit(0)

os.environ['BA_FX_OUTPUT'] = str(out)
sys.argv = ['export-cafe-effects.py', *icons]
v = runpy.run_path('scripts/export-cafe-effects.py')
env = v['env']

for prefix, _ in specs.values():
    for p in (W / 'selected').glob('character-' + prefix.lower() + '-*.bundle'):
        env.load_file(str(p))

for t in v['timelines']:
    t['controls'] = []
effects = {}
rows = []

for row in audit['missing']:
    go = next(
        o.read() for o in env.objects
        if o.type.name == 'GameObject' and o.assets_file.name.lower() == row['sourceCab'].lower() and o.path_id == row['sourceId']
    )
    name = f"{row['character']}__{go.m_Name}__embedded21"
    try:
        effects[name] = v['visit'](go)
    except Exception as err:
        print('SKIPPED embedded FX (missing dep):', name, err, flush=True)
        v['errors'].append({'effect': name, 'reason': str(err)})
        continue
    t = next(t for t in v['timelines'] if t['icon'] == row['icon'])
    binding_name = go.m_Name if row.get('kind') == 'character' else row.get('parent', go.m_Name)
    for start, end in row['windows']:
        t['controls'].append(dict(
            parents=[row['group']],
            track='Native embedded/persistent FX',
            prefab=name,
            existing=row.get('kind') == 'character',
            restartOnActivation=True,
            bindingResolved=True,
            binding=binding_name,
            start=start,
            duration=end - start,
            clipIn=0,
            speed=1,
            seed=0,
        ))
    rows.append(row)

(out / 'source.json').write_text(json.dumps(dict(timelines=v['timelines'], effects=effects, errors=v['errors'])), 'utf8')
(T / 'wave21-embedded-source.json').write_text(json.dumps(dict(roots=rows, errors=v['errors']), indent=2), 'utf8')
print('Native embedded/persistent roots:', len(rows), 'errors:', v['errors'])
