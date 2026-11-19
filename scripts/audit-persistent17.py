"""Check every active native persistent particle root of Wave 17 furniture scenes."""
from pathlib import Path
import json, sys, UnityPy
from glb import load

W = Path('.assets')
T = Path('test-results')
out_name = sys.argv[1] if len(sys.argv) > 1 else 'wave17-persistent-audit.json'
ids = set(json.loads(Path('scripts/roster-wave17.json').read_text('utf8')))
profiles = [p for p in json.loads((W / 'furniture-profiles.json').read_text('utf8')) if p['character'] in ids]
icons = {p['icon'] for p in profiles}
env = UnityPy.load(*map(str, [
    p for p in (W / 'selected').glob('*.bundle')
    if '-prefabs-' in p.name and (p.name.startswith('cafe-') or any(i.lower() in p.name.lower() for i in icons))
]))
prefabs = {}
for o in list(env.objects):
    if o.type.name != 'GameObject':
        continue
    go = o.read()
    if go.m_Name in icons and any(c.component.deref().type.name == 'PlayableDirector' for c in go.m_Component):
        prefabs[go.m_Name] = go

def roots(go, active=True, parent_ps=False):
    parts = {c.component.deref().type.name: c.component.deref() for c in go.m_Component}
    active = active and bool(go.m_IsActive)
    if not active:
        return
    if 'ParticleSystem' in parts and not parent_ps:
        yield go
    for ch in parts['Transform'].read().m_Children:
        yield from roots(ch.read().m_GameObject.read(), active, parent_ps or 'ParticleSystem' in parts)

rows = []
for key in sorted(ids):
    folder = W / 'wave17-final' / key
    c = json.loads((folder / 'character.json').read_text('utf8'))
    for f in c.get('furniture', []):
        d, _ = load(folder / f['model'])
        icon = f['sourceTimeline']
        native = list(roots(prefabs[icon]))
        rendered = {n for m in d['materials'] for n in m.get('extras', {}).get('BA_cafeParticle', {}).get('sourceName', '').split('/')}
        disabled = []
        for go in native:
            parts = {c.component.deref().type.name: c.component.deref() for c in go.m_Component}
            p = parts['ParticleSystem'].read_typetree()
            r = parts.get('ParticleSystemRenderer')
            t = parts['Transform'].read()
            if not p['EmissionModule']['enabled'] and r and not r.read().m_Enabled and not t.m_Children:
                disabled.append(dict(
                    root=go.m_Name,
                    reason='Native leaf has emission and renderer disabled',
                    sourceCab=go.object_reader.assets_file.name,
                    sourceId=go.object_reader.path_id,
                ))
        rows.append({
            'character': key,
            'id': f['id'],
            'icon': icon,
            'activePersistentRoots': [go.m_Name for go in native],
            'disabledLeafExclusions': disabled,
            'notParticleAdapted': [go.m_Name for go in native if go.m_Name not in rendered and go.m_Name not in {r['root'] for r in disabled}],
        })

activation = json.loads((T / 'activation035-source.json').read_text('utf8')) if (T / 'activation035-source.json').exists() else []
for row in rows:
    row['idleOnlyExclusions'] = [
        n for n in row['notParticleAdapted']
        if any(t['icon'] == row['icon'] and t['binding'] == n and t['path'][0] == 'Object_Idle' for t in activation)
    ]
result = {
    'prefabsScanned': len(prefabs),
    'rows': rows,
    'unexplained': [
        {'character': r['character'], 'id': r['id'], 'root': n}
        for r in rows for n in r['notParticleAdapted']
        if n not in r['idleOnlyExclusions']
    ],
}
(T / out_name).write_text(json.dumps(result, indent=2), 'utf8')
print('Persistent audit:', len(rows), 'scenes,', len(result['unexplained']), 'unexplained')
if result['unexplained']:
    print(json.dumps(result['unexplained'], indent=2))
