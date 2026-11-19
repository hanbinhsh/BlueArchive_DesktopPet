"""Preserve previously reviewed profiles while adding Wave 20 scene bindings."""
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
W = R / '.assets'
B = W / 'pre-wave20'

def read(p): return json.loads(p.read_text('utf8'))
def write(p, v): p.write_text(json.dumps(v, ensure_ascii=False, indent=2), 'utf8')

ids = set(read(R / 'scripts/roster-wave20.json'))

def identity(p):
    return (p['character'], p['icon'], p['group'], p['studentTrack']['name'])

resolved = read(W / 'furniture-profiles.json')
new_groups = {(p['icon'], p['group']) for p in resolved if p['character'] in ids}
required = [p for p in resolved if p['character'] in ids or (p['icon'], p['group']) in new_groups]
merged = {identity(p): p for p in read(B / 'furniture-profiles.json')}
merged.update({identity(p): p for p in required})
profiles = list(merged.values())
write(W / 'furniture-profiles.json', profiles)

new = read(W / 'furniture-bindings.json')
bindings = read(B / 'furniture-bindings.json')
for p in profiles:
    if identity(p) not in {identity(q) for q in required}:
        continue
    for name in [p['root']] + [t['binding'] for t in p['furnitureTracks']]:
        bindings[name] = sorted(set(bindings.get(name, [])) | set(new.get(name, [])))
write(W / 'furniture-bindings.json', bindings)

icons = {p['icon'] for p in profiles if p['character'] in ids}
write(
    W / 'furniture-timelines.json',
    [p for p in read(B / 'furniture-timelines.json') if p['icon'] not in icons]
    + [p for p in read(W / 'furniture-timelines.json') if p['icon'] in icons],
)
write(R / 'test-results/wave20-furniture-profiles.json', [p for p in profiles if p['character'] in ids])
print('Preserved old profiles; added', sum(p['character'] in ids for p in profiles), 'Wave 20 furniture profiles')
