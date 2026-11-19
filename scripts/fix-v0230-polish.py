"""Polish v0.2.30: uncover saori_dress live mirror (remove beige placeholder cafe_particle_9) & fix ako_dress sofa yaw."""
import json, pathlib
import numpy as np
from glb import load, save, compact

R = pathlib.Path(__file__).resolve().parents[1]

# 1. Remove opaque placeholder cafe_particle_9 covering saori_dress live PlanarMirror
gp = R / 'characters/saori_dress/f210366_0.glb'
d, b = load(gp)
removed = []
for n in d['nodes']:
    if 'children' in n:
        kept = []
        for ci in n['children']:
            cn = d['nodes'][ci]
            if cn.get('name') == 'cafe_particle_9':
                removed.append(ci)
            else:
                kept.append(ci)
        n['children'] = kept
# Ensure mirror_rt_plane is right in front of the mirror backing at X=0.505 (facing -X toward Saori)
for n in d['nodes']:
    if n.get('name') == 'mirror_rt_plane':
        n['translation'] = [0.505, 0.5291, 0.004]
compact(d, b)
save(gp, d, b)
print(f'Uncovered saori_dress live PlanarMirror (removed placeholder nodes {removed})')

# 2. Set ako_dress f15306_0 & f15306_1 yaw = 0.785398 (3/4 view facing Ako's face, matching Image 3)
ako_p = R / 'characters/ako_dress/character.json'
ako = json.loads(ako_p.read_text('utf8'))
for f in ako.get('furniture', []):
    if f['id'] in ('f15306_0', 'f15306_1'):
        f['yaw'] = 0.785398
ako_p.write_text(json.dumps(ako, ensure_ascii=False, indent=2) + '\n', 'utf8')

yaw_p = R / 'scripts/furniture-character-view-yaw.json'
ym = json.loads(yaw_p.read_text('utf8'))
ym.setdefault('ako_dress', {})['f15306_0'] = round(0.785398 - 2.356194490192345, 6)
ym['ako_dress']['f15306_1'] = round(0.785398 - 2.356194490192345, 6)
yaw_p.write_text(json.dumps(dict(sorted(ym.items())), ensure_ascii=False, indent=2) + '\n', 'utf8')
print('Updated ako_dress f15306_0 & f15306_1 yaw to 0.785398 (3/4 front facing Ako)')
