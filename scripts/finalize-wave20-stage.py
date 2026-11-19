"""Merge expanded actions into wave20-final, fix saori_dress Cafe handgun visibility, and set verified viewYaws."""
import json, math, shutil
from pathlib import Path
from glb import load, save

R = Path(__file__).resolve().parents[1]
W = R / '.assets'
T = R / 'test-results'
expanded = W / 'expanded-ready'
stage = W / 'wave20-final'

specs = json.loads((R / 'scripts/roster-wave20.json').read_text('utf8'))
yaw_file = R / 'scripts/furniture-character-view-yaw.json'
yaw_map = json.loads(yaw_file.read_text('utf8'))

# 1. Merge expanded model.glb and actions/framing from .assets/expanded-ready into .assets/wave20-final
total_actions = 0
for key in specs:
    src_dir = expanded / key
    dst_dir = stage / key
    shutil.copy2(src_dir / 'model.glb', dst_dir / 'model.glb')
    src_c = json.loads((src_dir / 'character.json').read_text('utf8'))
    dst_c = json.loads((dst_dir / 'character.json').read_text('utf8'))
    for field in ['actions', 'animations', 'framing', 'mouth', 'eyeBounds', 'source', 'defaultAction']:
        if field in src_c:
            dst_c[field] = src_c[field]
    (dst_dir / 'character.json').write_text(json.dumps(dst_c, ensure_ascii=False, indent=2) + '\n', 'utf8')
    total_actions += len(dst_c['actions'])
print(f'Merged expanded models/actions for {len(specs)} Wave 20 outfits ({total_actions} total actions)')

# 2. Fix saori_dress (CH0259): hide combat-only Handgun & HandGrenade meshes in Cafe clips & Cafe mirror furniture
#    (In-game Cafe loads CH0259_CafeOnly which omits Saori_Original_Handgun and CH0259_HandGrenade_Mesh.)
saori_model = stage / 'saori_dress/model.glb'
d, b = load(saori_model)
hide_nodes = [i for i, n in enumerate(d['nodes']) if n.get('name') in ('Saori_Original_Handgun', 'CH0259_HandGrenade_Mesh')]
vis = d['scenes'][0].setdefault('extras', {}).setdefault('BA_pet_visibility', {'defaults': {}, 'clips': {}})
for anim in d['animations']:
    if '_Cafe_' in anim['name']:
        clip_tracks = vis['clips'].setdefault(anim['name'], [])
        existing = {tr['node'] for tr in clip_tracks}
        for ni in hide_nodes:
            if ni not in existing:
                clip_tracks.append({'node': ni, 'keys': [[0.0, False]]})
save(saori_model, d, b)
print(f'Hidden {hide_nodes} (Handgun/HandGrenade) in saori_dress Cafe clips')

saori_furn = stage / 'saori_dress/f210366_0.glb'
fd, fb = load(saori_furn)
f_hide = [i for i, n in enumerate(fd['nodes']) if n.get('name') in ('Saori_Original_Handgun', 'CH0259_HandGrenade_Mesh')]
f_vis = fd['scenes'][0].setdefault('extras', {}).setdefault('BA_pet_visibility', {'defaults': {}, 'clips': {}})
for ni in f_hide:
    f_vis['defaults'][str(ni)] = False
save(saori_furn, fd, fb)
print(f'Hidden {f_hide} (Handgun/HandGrenade) in saori_dress/f210366_0.glb')

# 3. Record verified front-facing viewYaws (base viewYaw + chosen delta from 4-angle contact sheets)
deltas = {
    ('misaki', 'f1108_0'): -math.pi / 2,
    ('shokuhou_misaki', 'f210323_0'): 0.0,
    ('misaki_swimsuit', 'f17105_0'): 0.0,
    ('akari_newyear', 'f210334_0'): 0.0,
    ('ayane', 'f11206_0'): -math.pi / 2,
    ('ayane_swimsuit', 'f4103_0'): -math.pi / 2,
    ('kokoro', 'f211314_0'): 0.0,
    ('kokoro', 'f211314_1'): 0.0,
    ('izumi_newyear', 'f210361_0'): -math.pi / 2,
    ('saori', 'f1108_0'): -math.pi / 2,
    ('saori_swimsuit', 'f17304_0'): 0.0,
    ('saori_dress', 'f210366_0'): 0.0,
    ('shizuko', 'f203302_0'): -math.pi / 2,
    ('shizuko_swimsuit', 'f9302_0'): math.pi,
    ('kotone', 'f211314_0'): 0.0,
    ('kotone', 'f211314_1'): 0.0,
    ('tsukuyo', 'f4106_0'): -math.pi / 2,
    ('tsukuyo_dress', 'f210389_0'): 0.0,  # will verify at t=40s
}

for key in specs:
    cp = stage / key / 'character.json'
    c = json.loads(cp.read_text('utf8'))
    changed = False
    for f in c.get('furniture', []):
        fid = f['id']
        base = float(f.get('viewYaw', 0.0))
        if (key, fid) in deltas:
            # Normalize to (-pi, pi]
            val = base + deltas[(key, fid)]
            while val > math.pi:
                val -= 2 * math.pi
            while val <= -math.pi:
                val += 2 * math.pi
            val = round(val, 6)
            print(f'  viewYaw {key:18s} {fid:10s}: base={base:.4f} -> {val:.4f}')
            f['viewYaw'] = val
            yaw_map.setdefault(key, {})[fid] = val
            changed = True
    if changed:
        cp.write_text(json.dumps(c, ensure_ascii=False, indent=2) + '\n', 'utf8')

yaw_file.write_text(json.dumps(dict(sorted(yaw_map.items())), ensure_ascii=False, indent=2) + '\n', 'utf8')

# 4. Write check2 rows for tsukuyo_dress at t=40s (4 angles) + saori_dress f210366_0 (yaw 0 & -pi/2)
check2 = [
    dict(character='tsukuyo_dress', id='f210389_0', status='ready', times=[40.0], yaw=yaw)
    for yaw in [0, math.pi / 2, math.pi, math.pi * 1.5]
] + [
    dict(character='saori_dress', id='f210366_0', status='ready', times=[5.0], yaw=0),
    dict(character='saori_dress', id='f210366_0', status='ready', times=[5.0], yaw=math.pi * 1.5),
]
(T / 'wave20-check2-rows.json').write_text(json.dumps(check2), 'utf8')
print('Wrote wave20-check2-rows.json (6 rows)')
