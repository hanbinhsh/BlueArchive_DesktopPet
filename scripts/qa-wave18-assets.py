"""Verify Wave 18 (+ Yukino, NP0283, Toki, and Field-Cafe furniture on Hina/Hina Dress/Seia) integrity."""
import json, hashlib
from pathlib import Path
from glb import load, read_accessor

R = Path(__file__).resolve().parents[1]
T = R / 'test-results'
stage = R / '.assets/wave18-final'
read = lambda p: json.loads(p.read_text('utf8'))

# Update np0283 display name
np_p = stage / 'np0283/character.json'
np_m = read(np_p)
np_m['name'] = '妮可 · 探索'
np_p.write_text(json.dumps(np_m, ensure_ascii=False, indent=2), 'utf8')

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

profiles = read(R / 'scripts/wave18-profiles.json')
specs = read(R / 'scripts/roster-wave18-all.json')
index = read(T / 'action-source-index.json')
rows = []

for key in list(specs) + ['toki', 'hina', 'hina_dress', 'seia']:
    c = read(stage / key / 'character.json')
    d, b = load(stage / key / 'model.glb')
    curves = 0
    if key in specs:
        meta = {x['track']: x for x in d['scenes'][0]['extras']['BAAD_unity_animation']['clips']}
        sources = []
        for entry in index[key]:
            p = R / entry['path']
            sd, sb = load(p)
            sources.append((p, sd, sb, {x['track']: x for x in sd['scenes'][0]['extras']['BAAD_unity_animation']['clips']}))
        for action in c['actions']:
            name = action['clip']
            matches = [
                s for s in sources
                if s[3].get(name) == meta[name] and any(a['name'] == name for a in s[1].get('animations', []))
            ]
            assert matches, (key, name)
            source, sd, sb, _ = matches[0]
            a = next(a for a in d['animations'] if a['name'] == name)
            sa = next(a for a in sd['animations'] if a['name'] == name)
            assert len(a['channels']) == len(sa['channels'])
            for x, y in zip(a['channels'], sa['channels']):
                assert x['target']['path'] == y['target']['path'] and d['nodes'][x['target']['node']]['name'] == sd['nodes'][y['target']['node']]['name']
                xs = a['samplers'][x['sampler']]
                ys = sa['samplers'][y['sampler']]
                assert xs.get('interpolation') == ys.get('interpolation')
                for prop in ['input', 'output']:
                    assert read_accessor(d, b, xs[prop]) == read_accessor(sd, sb, ys[prop]), (key, name, prop)
                curves += 1
        assert d['scenes'][0]['extras'].get('BA_halo_follow') or profiles[key].get('noHalo')
        assert any('halo' in n.get('name', '').lower() and 'mesh' in n for n in d['nodes']) or profiles[key].get('noHalo')
        assert c.get('mouth') or profiles[key].get('noMouthAtlas')
    assert not any(x.get('uri') for x in d.get('buffers', []) + d.get('images', []))
    assert (stage / key / 'thumbnail.png').is_file()
    for f in c.get('furniture', []):
        fd, fb = load(stage / key / f['model'])
        assert any(a['name'] == f['clip'] for a in fd['animations']), (key, f['id'])
        assert f['duration'] > 0
        assert not any(x.get('uri') for x in fd.get('buffers', []) + fd.get('images', []))
    rows.append(dict(
        character=key,
        actions=len(c['actions']),
        furniture=len(c.get('furniture', [])),
        unchangedAuthoredChannels=curves,
        modelSha256=sha(stage / key / 'model.glb'),
    ))

framing = [r for r in read(T / 'expanded-framing.json') if r['character'] in specs or r['character'] == 'toki']
(T / 'wave18-framing.json').write_text(json.dumps(framing, indent=2), 'utf8')
added_rows = [r for r in rows if r['character'] in specs]
updated_rows = [r for r in rows if r['character'] not in specs]
report = dict(
    added=added_rows,
    updated=updated_rows,
    baseVersion='0.2.26',
    totalNewActions=sum(r['actions'] for r in added_rows),
    totalNewFurniture=sum(r['furniture'] for r in added_rows) + sum(len([f for f in read(stage / r['character'] / 'character.json').get('furniture', []) if f['id'].startswith('field_')]) for r in updated_rows),
)
(T / 'wave18-resources.json').write_text(json.dumps(report, indent=2), 'utf8')
print('QA PASSED:', len(added_rows), 'new outfits +', len(updated_rows), 'updated outfits,', report['totalNewActions'], 'new actions,', report['totalNewFurniture'], 'new furniture,', sum(r['unchangedAuthoredChannels'] for r in added_rows), 'verified channels')
