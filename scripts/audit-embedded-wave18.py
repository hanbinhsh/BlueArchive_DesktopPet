"""Find active character-embedded particles missing from Wave 18 furniture models."""
from pathlib import Path
import json, sys, UnityPy
from glb import load
from source_dependencies import resolve_cached

R = Path(__file__).resolve().parents[1]
W = R / '.assets'
T = R / 'test-results'
stage = W / 'wave18-final'
out_name = sys.argv[1] if len(sys.argv) > 1 else 'wave18-embedded-audit.json'
specs = json.loads((R / 'scripts/roster-wave18.json').read_text('utf8'))
profiles = [p for p in json.loads((W / 'furniture-profiles.json').read_text('utf8')) if p['character'] in specs]
files = [
    p for p in (W / 'selected').glob('*.bundle')
    if '-prefabs-' in p.name and (
        any(p.name.startswith('character-' + prefix.lower() + '-') for prefix, _ in specs.values())
        or p.name.startswith('cafe-')
    )
]
env = UnityPy.load(*map(str, files))
objects = list(env.objects)
roots = {}
rows = []

def read(p):
    return resolve_cached(env, p.read)

def hierarchy(go, path='', parents=()):
    parts = {c.component.deref().type.name: c.component.deref() for c in go.m_Component}
    path = (path + '/' + go.m_Name).lstrip('/')
    row = dict(go=go, path=path, parents=parents, parts=parts)
    yield row
    for p in read(parts['Transform']).m_Children:
        yield from hierarchy(read(read(p).m_GameObject), path, parents + (row,))

for p in profiles:
    if p['root'] in roots:
        continue
    candidates = []
    for o in objects:
        if o.type.name == 'GameObject' and o.read().m_Name == p['root']:
            nodes = list(hierarchy(o.read()))
            score = sum(
                sum(bool(ptr.m_PathID) for ptr in read(n['parts']['ParticleSystemRenderer']).m_Materials)
                for n in nodes if 'ParticleSystemRenderer' in n['parts']
            )
            candidates.append((score, nodes))
    assert candidates, p['root']
    roots[p['root']] = max(candidates, key=lambda r: r[0])[1]

for p in profiles:
    cp = stage / p['character'] / 'character.json'
    c = json.loads(cp.read_text('utf8'))
    f = next(
        f for f in c.get('furniture', [])
        if f['sourceTimeline'] == p['icon'] and f['sourceGroup'] == p['group'] and f['sourceStudentTrack'] == p['studentTrack']['name']
    )
    d, b = load(cp.parent / f['model'])
    metadata = d['scenes'][0]['extras']['BAAD_unity_animation']['clips'][0]
    curves = {x['path']: x['keys'] for x in metadata['unity_curves'] if x['attribute'] == 'm_IsActive'}
    nodes = roots[p['root']]
    times = sorted({0.0, f['duration'], *[k[0] for keys in curves.values() for k in keys if 0 <= k[0] <= f['duration']]})
    rendered = {n for m in d['materials'] for n in m.get('extras', {}).get('BA_cafeParticle', {}).get('sourceName', '').split('/')}

    def active(n, t):
        path = n['path'].partition('/')[2]
        value = bool(n['go'].m_IsActive)
        for time, state, *_ in curves.get(path, []):
            if time > t + 1e-7:
                break
            value = state >= 0.5
        return value

    for node in nodes:
        if 'ParticleSystem' not in node['parts'] or any('ParticleSystem' in n['parts'] for n in node['parents']):
            continue
        chain = [*node['parents'], node]
        windows = []
        for a, z in zip(times, times[1:]):
            if z > a and all(active(n, a) for n in chain):
                if windows and abs(windows[-1][1] - a) < 1e-7:
                    windows[-1][1] = z
                else:
                    windows.append([a, z])
        if not windows:
            continue
        row = dict(
            character=p['character'],
            id=f['id'],
            icon=p['icon'],
            group=p['group'],
            root=p['root'],
            path=node['path'].partition('/')[2],
            name=node['go'].m_Name,
            windows=windows,
            alreadyAdapted=node['go'].m_Name in rendered,
            sourceCab=node['go'].object_reader.assets_file.name,
            sourceId=node['go'].object_reader.path_id,
        )
        rows.append(row)

report = dict(rows=rows, missing=[r for r in rows if not r['alreadyAdapted']])
(T / out_name).write_text(json.dumps(report, indent=2), 'utf8')
print('Embedded audit:', len(rows), 'active,', len(report['missing']), 'missing')
if report['missing']:
    print(json.dumps(report['missing'], indent=2))
