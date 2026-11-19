"""Restore the original simulation-space field without changing model buffers."""
from pathlib import Path
import json
import shutil
from glb import load, save

source = json.loads(Path('.assets/cafe-fx-audit032/source.json').read_text('utf8'))
spaces = {}
def visit(value):
    if isinstance(value, dict):
        if 'particle' in value and 'path' in value:
            space = value['particle'].get('moveWithTransform', 0)
            assert space in (0, 1), (value['path'], space)
            if value['path'] in spaces:
                assert spaces[value['path']] == space
            spaces[value['path']] = space
        for child in value.values(): visit(child)
    elif isinstance(value, list):
        for child in value: visit(child)
visit(source['effects'])
rows = []
for manifest in Path('characters').glob('*/character.json'):
    character = json.loads(manifest.read_text('utf8'))
    for name in sorted({f['model'] for f in character.get('furniture', [])}):
        file = manifest.parent / name
        doc, binary = load(file)
        count = world = 0
        for material in doc['materials']:
            spec = material.get('extras', {}).get('BA_cafeParticle')
            if not spec: continue
            spec['simulationSpace'] = spaces[spec['sourceName']]
            count += 1
            world += spec['simulationSpace'] == 1
        if not count: continue
        backup = Path('.assets/pre032-gravity') / manifest.parent.name / name
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists(): shutil.copyfile(file, backup)
        save(file, doc, binary)
        rows.append({'character': manifest.parent.name, 'model': name, 'particles': count, 'worldParticles': world})
Path('test-results/particle-space032.json').write_text(json.dumps(rows, indent=2), 'utf8')
print('Models:', len(rows), 'world particles:', sum(r['worldParticles'] for r in rows))
