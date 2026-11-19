"""Fix v0.2.29 bugs:
1. Attach 4 audited persistent furniture ParticleSystems (megu duck_01_Bubble, hanae_christmas FireLoop, kanna Smoke_01, pina_guide TV_Loop_1).
2. Keep megu/f6301_0 duck_02_Bubble (and duck_01_Bubble emitter) strictly horizontal on the bathtub water surface instead of tilting with the bobbing ducks.
3. Clip hanae_christmas/f207308_0 rabbit/toys (CH0195_SkillProp) and gift boxes (gift_box_01..03) at the Cafe floor plane (Y >= 0.008) via BA_liquidReceiver, and clamp negative scale overshoot.
"""
import copy, json, math, os, pathlib, runpy, sys
import numpy as np
from glb import load, save, read_accessor, append_accessor, compact

R = pathlib.Path(__file__).resolve().parents[1]
W = R / '.assets'

# --- Step 1: Export & attach the 4 missing persistent furniture ParticleSystems ---
PERSISTENT_TARGETS = [
    ('megu', 'f6301_0', 'my_hotsprings_01_woodenbathtub', 'FX_my_hotsprings_woodenbathtub_duck_01_Bubble'),
    ('hanae_christmas', 'f207308_0', 'my_event13_fireplace', 'FX_my_event13_fireplace_FireLoop'),
    ('kanna', 'f207313_0', 'my_event15_table', 'FX_my_event15_table_Smoke_01'),
    ('pina_guide', 'f210368_0', 'my_event078_videotelevision', 'FX_my_event078_videotelevision_TV_Loop_1'),
]

out_dir = W / 'cafe-persistent-v0229'
out_dir.mkdir(exist_ok=True)
icons = sorted({ic for _, _, ic, _ in PERSISTENT_TARGETS})
os.environ['BA_FX_OUTPUT'] = str(out_dir)
sys.argv = ['export-cafe-effects.py', *icons]
v = runpy.run_path(str(R / 'scripts/export-cafe-effects.py'))
env = v['env']
read_obj = v['read']

def hierarchy(go):
    yield go
    t = next(read_obj(c.component) for c in go.m_Component if c.component.deref().type.name == 'Transform')
    for ch in t.m_Children:
        yield from hierarchy(read_obj(read_obj(ch).m_GameObject))

def score(go):
    total = 0
    for g in hierarchy(go):
        for c in g.m_Component:
            if c.component.deref().type.name in ['ParticleSystemRenderer', 'MeshRenderer', 'SkinnedMeshRenderer']:
                total += sum(bool(p.m_PathID) for p in read_obj(c.component).m_Materials)
    return total

for t in v['timelines']:
    t['controls'] = []
effects = {}

for ch, fid, icon, root_name in PERSISTENT_TARGETS:
    manifest = json.loads((R / 'characters' / ch / 'character.json').read_text('utf8'))
    f = next(x for x in manifest['furniture'] if x['id'] == fid)
    d_check, _ = load(R / 'characters' / ch / f['model'])
    already = any(root_name in m.get('extras', {}).get('BA_cafeParticle', {}).get('sourceName', '') for m in d_check['materials'])
    if already:
        print(f'Already present: {ch}/{fid} {root_name}')
        continue
    roots_list = [
        o.read() for o in env.objects
        if o.type.name == 'GameObject' and o.read().m_Name == icon
        and any(c.component.deref().type.name == 'PlayableDirector' for c in o.read().m_Component)
    ]
    prefab = max(roots_list, key=score)
    go = next(g for g in hierarchy(prefab) if g.m_Name == root_name)
    key_name = f'{icon}__{root_name}__persistent29'
    effects[key_name] = v['visit'](go)
    # Find parent bone name in prefab for accurate binding
    parent_tr = next(read_obj(c.component) for c in go.m_Component if c.component.deref().type.name == 'Transform').m_Father
    parent_name = read_obj(read_obj(parent_tr).m_GameObject).m_Name if parent_tr.m_PathID else icon
    next(t for t in v['timelines'] if t['icon'] == icon)['controls'].append(dict(
        parents=[f['sourceGroup']],
        track='Native persistent FX',
        prefab=key_name,
        existing=True,
        bindingResolved=True,
        binding=root_name,
        start=0.0,
        duration=f['duration'],
        clipIn=0.0,
        speed=1.0,
        seed=0,
    ))
    print(f'Exported persistent FX: {ch}/{fid} {root_name} (parent={parent_name})')

(out_dir / 'source.json').write_text(json.dumps(dict(timelines=v['timelines'], effects=effects, errors=v['errors'])), 'utf8')
if effects:
    os.environ['BA_FX_SOURCE'] = str(out_dir)
    os.environ['BA_FX_STAGE'] = str(R / 'characters')
    os.environ['BA_FX_APPEND'] = '1'
    chars_to_attach = sorted({ch for ch, fid, icon, rn in PERSISTENT_TARGETS if f'{icon}__{rn}__persistent29' in effects})
    sys.argv = ['prepare-cafe-effects.py', *chars_to_attach]
    runpy.run_path(str(R / 'scripts/prepare-cafe-effects.py'))

# --- Helper math for GLB world transforms ---
def q_mul(q1, q2):
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return np.array([
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
    ], dtype=float)

def q_inv(q):
    n = np.dot(q, q)
    return np.array([-q[0], -q[1], -q[2], q[3]], dtype=float) / max(n, 1e-12)

def q_rot_vec(q, v):
    x, y, z, w = q
    u = np.array([x, y, z], dtype=float)
    return v + 2.0 * np.cross(u, np.cross(u, v) + w * v)

def trs_to_mat(t, q, s):
    x, y, z, w = q
    R3 = np.array([
        [1 - 2*(y*y + z*z), 2*(x*y - z*w), 2*(x*z + y*w)],
        [2*(x*y + z*w), 1 - 2*(x*x + z*z), 2*(y*z - x*w)],
        [2*(x*z - y*w), 2*(y*z + x*w), 1 - 2*(x*x + y*y)],
    ], dtype=float)
    M = np.eye(4, dtype=float)
    M[:3, :3] = R3 * np.array(s, dtype=float)[None, :]
    M[:3, 3] = np.array(t, dtype=float)
    return M

def mat_to_quat(R3):
    # Normalize columns first
    cols = [R3[:, i] / max(np.linalg.norm(R3[:, i]), 1e-12) for i in range(3)]
    M = np.column_stack(cols)
    tr = M[0,0] + M[1,1] + M[2,2]
    if tr > 0:
        S = math.sqrt(tr + 1.0) * 2
        w = 0.25 * S; x = (M[2,1] - M[1,2]) / S; y = (M[0,2] - M[2,0]) / S; z = (M[1,0] - M[0,1]) / S
    elif M[0,0] > M[1,1] and M[0,0] > M[2,2]:
        S = math.sqrt(1.0 + M[0,0] - M[1,1] - M[2,2]) * 2
        w = (M[2,1] - M[1,2]) / S; x = 0.25 * S; y = (M[0,1] + M[1,0]) / S; z = (M[0,2] + M[2,0]) / S
    elif M[1,1] > M[2,2]:
        S = math.sqrt(1.0 + M[1,1] - M[0,0] - M[2,2]) * 2
        w = (M[0,2] - M[2,0]) / S; x = (M[0,1] + M[1,0]) / S; y = 0.25 * S; z = (M[1,2] + M[2,1]) / S
    else:
        S = math.sqrt(1.0 + M[2,2] - M[0,0] - M[1,1]) * 2
        w = (M[1,0] - M[0,1]) / S; x = (M[0,2] + M[2,0]) / S; y = (M[1,2] + M[2,1]) / S; z = 0.25 * S
    q = np.array([x, y, z, w], dtype=float)
    return q / max(np.linalg.norm(q), 1e-12)

# --- Step 2: Fix megu/f6301_0 duck_02_Bubble tilt & duck_01_Bubble water-surface height ---
megu_path = R / 'characters/megu/f6301_0.glb'
doc, raw = load(megu_path)
data = bytearray(raw)
parents = {}
for i, n in enumerate(doc['nodes']):
    for ch in n.get('children', []):
        parents[ch] = i

def sample_node_tracks(doc, data, anim):
    tracks = {}
    for ch in anim['channels']:
        ni = ch['target']['node']; path = ch['target']['path']
        s = anim['samplers'][ch['sampler']]
        ts = np.array(read_accessor(doc, data, s['input']))[:, 0]
        vs = np.array(read_accessor(doc, data, s['output']), dtype=float)
        tracks[(ni, path)] = (ts, vs)
    return tracks

def eval_trs(doc, tracks, ni, t):
    n = doc['nodes'][ni]
    out = {}
    for path, default in [('translation', [0,0,0]), ('rotation', [0,0,0,1]), ('scale', [1,1,1])]:
        if (ni, path) in tracks:
            ts, vs = tracks[(ni, path)]
            idx = int(np.searchsorted(ts, t, side='right') - 1)
            idx = max(0, min(idx, len(ts) - 1))
            nxt = min(idx + 1, len(ts) - 1)
            span = ts[nxt] - ts[idx]
            u = 0.0 if span <= 1e-9 else float(np.clip((t - ts[idx]) / span, 0.0, 1.0))
            a, b = vs[idx], vs[nxt]
            if path == 'rotation':
                if np.dot(a, b) < 0: b = -b
                v = a * (1 - u) + b * u
                v /= max(np.linalg.norm(v), 1e-12)
            else:
                v = a * (1 - u) + b * u
            out[path] = v
        else:
            out[path] = np.array(n.get(path, default), dtype=float)
    return out['translation'], out['rotation'], out['scale']

def world_mat(doc, tracks, ni, t):
    chain = []
    cur = ni
    while cur is not None:
        chain.append(cur)
        cur = parents.get(cur)
    M = np.eye(4, dtype=float)
    for idx in reversed(chain):
        tr, rot, sc = eval_trs(doc, tracks, idx, t)
        M = M @ trs_to_mat(tr, rot, sc)
    return M

anim = doc['animations'][0]
tracks = sample_node_tracks(doc, data, anim)

# Measure bathtub water surface world Y at t=0
water_node = next(i for i, n in enumerate(doc['nodes']) if 'my_hotsprings_01_woodenbathtub_water' in n.get('name', ''))
water_mesh = doc['meshes'][doc['nodes'][water_node]['mesh']]
water_pos = np.array(read_accessor(doc, data, water_mesh['primitives'][0]['attributes']['POSITION']), dtype=float)
M_water = world_mat(doc, tracks, water_node, 0.0)
water_world_ys = (water_pos @ M_water[:3, :3].T + M_water[:3, 3])[:, 1]
water_y = float(np.median(water_world_ys))
print(f'megu bathtub water surface Y = {water_y:.4f} (min={water_world_ys.min():.4f}, max={water_world_ys.max():.4f})')

# Check Duck02 bubble mesh local plane normal so we orient it strictly horizontal (+Y in world)
duck2_bubble = next(i for i, n in enumerate(doc['nodes']) if 'duck_02_Bubble' in n.get('name', ''))
duck2_parent = parents[duck2_bubble]
b_mesh = doc['meshes'][doc['nodes'][duck2_bubble]['mesh']]
b_verts = np.array(read_accessor(doc, data, b_mesh['primitives'][0]['attributes']['POSITION']), dtype=float)
# Identify which local axis of the quad mesh has ~0 extent (the plane normal!)
extents = b_verts.max(axis=0) - b_verts.min(axis=0)
flat_axis = int(np.argmin(extents))
print(f'duck_02_Bubble local extents={extents.round(4)} flat_axis={flat_axis}')
# Build desired world rotation that puts local flat_axis along world +Y (horizontal!)
# Wait: for flat_axis=2 (XY quad in local space), rotating -90 deg around X maps local +Z -> world +Y!
# For flat_axis=1 (XZ quad), identity maps local +Y -> world +Y!
if flat_axis == 2:
    # Rotate around X by -pi/2 so local (0,0,1) -> (0,1,0)
    desired_world_q = np.array([-math.sin(math.pi/4), 0.0, 0.0, math.cos(math.pi/4)], dtype=float)
elif flat_axis == 0:
    desired_world_q = np.array([0.0, 0.0, math.sin(math.pi/4), math.cos(math.pi/4)], dtype=float)
else:
    desired_world_q = np.array([0.0, 0.0, 0.0, 1.0], dtype=float)

# Bake local translation & rotation onto duck2_bubble at 30 Hz so it stays strictly horizontal at water_y + 0.004
# while following Duck02's exact world XZ center!
sample_times = np.array(read_accessor(doc, data, anim['samplers'][anim['channels'][0]['sampler']]['input']))[:, 0]
local_ts = []
local_qs = []
orig_local_pos = np.array(doc['nodes'][duck2_bubble].get('translation', [0, 0, 0]), dtype=float)
prev_q = None
for t in sample_times:
    M_par = world_mat(doc, tracks, duck2_parent, float(t))
    M_par_inv = np.linalg.inv(M_par)
    par_world_pos = M_par[:3, 3]
    par_world_q = mat_to_quat(M_par[:3, :3])
    # Place ripple right at Duck02's world XZ and bathtub water_y + 0.004
    target_world_pos = np.array([par_world_pos[0], water_y + 0.004, par_world_pos[2], 1.0], dtype=float)
    loc_p = (M_par_inv @ target_world_pos)[:3]
    # Counter-rotate parent world rotation so bubble world rotation == desired_world_q (horizontal!)
    loc_q = q_mul(q_inv(par_world_q), desired_world_q)
    if prev_q is not None and np.dot(loc_q, prev_q) < 0:
        loc_q = -loc_q
    prev_q = loc_q
    local_ts.append(loc_p.tolist())
    local_qs.append(loc_q.tolist())

# Remove any existing channels on duck2_bubble and append baked horizontal tracks
anim['channels'] = [c for c in anim['channels'] if c['target']['node'] != duck2_bubble]
t_acc = append_accessor(doc, data, [(float(t),) for t in sample_times], 'SCALAR')
doc['accessors'][t_acc]['min'] = [float(sample_times[0])]
doc['accessors'][t_acc]['max'] = [float(sample_times[-1])]
p_acc = append_accessor(doc, data, local_ts, 'VEC3')
q_acc = append_accessor(doc, data, local_qs, 'VEC4')
anim['channels'].append({'sampler': len(anim['samplers']), 'target': {'node': duck2_bubble, 'path': 'translation'}})
anim['samplers'].append({'input': t_acc, 'output': p_acc, 'interpolation': 'LINEAR'})
anim['channels'].append({'sampler': len(anim['samplers']), 'target': {'node': duck2_bubble, 'path': 'rotation'}})
anim['samplers'].append({'input': t_acc, 'output': q_acc, 'interpolation': 'LINEAR'})
doc['nodes'][duck2_bubble]['translation'] = local_ts[0]
doc['nodes'][duck2_bubble]['rotation'] = local_qs[0]

# Also pin duck_01_Bubble emitter container node to water_y + 0.005 so Duck01's World-aligned horizontal ripples stay on the water plane!
duck1_emitters = [i for i, n in enumerate(doc['nodes']) if 'duck_01_Bubble' in n.get('name', '') and n.get('name', '').startswith('cafe_fx_')]
for em_idx in duck1_emitters:
    em_par = parents[em_idx]
    em_ts = []
    for t in sample_times:
        M_par = world_mat(doc, tracks, em_par, float(t))
        M_par_inv = np.linalg.inv(M_par)
        par_world_pos = M_par[:3, 3]
        target_world_pos = np.array([par_world_pos[0], water_y + 0.005, par_world_pos[2], 1.0], dtype=float)
        em_ts.append((M_par_inv @ target_world_pos)[:3].tolist())
    anim['channels'] = [c for c in anim['channels'] if not (c['target']['node'] == em_idx and c['target']['path'] == 'translation')]
    ep_acc = append_accessor(doc, data, em_ts, 'VEC3')
    anim['channels'].append({'sampler': len(anim['samplers']), 'target': {'node': em_idx, 'path': 'translation'}})
    anim['samplers'].append({'input': t_acc, 'output': ep_acc, 'interpolation': 'LINEAR'})
    doc['nodes'][em_idx]['translation'] = em_ts[0]
    print(f'Pinned Duck01 emitter node {em_idx} ({doc["nodes"][em_idx]["name"]}) to water_y={water_y + 0.005:.4f}')

# Also make duck_02_Bubble doubleSided so it is visible from both top and underside water angles
for pr in b_mesh['primitives']:
    doc['materials'][pr['material']]['doubleSided'] = True

save(megu_path, doc, compact(doc, data))
print('Saved fixed megu/f6301_0.glb')

# --- Step 3: Fix hanae_christmas/f207308_0 floor clipping & negative scale overshoot ---
hanae_path = R / 'characters/hanae_christmas/f207308_0.glb'
hdoc, hraw = load(hanae_path)
hdata = bytearray(hraw)

floor_spec = {
    'node': 'furniture_0_my_event13_fireplace',
    'normal': [0.0, 1.0, 0.0],
    'constant': -0.008,
}

# 3a. Attach floor clip to my_event13_CH0195_Prop (rabbit, train, horse)
for m in hdoc['materials']:
    if m.get('name') == 'my_event13_CH0195_Prop':
        m.setdefault('extras', {})['BA_liquidReceiver'] = dict(floor_spec)
        print('Added BA_liquidReceiver floor clip to my_event13_CH0195_Prop')

# 3b. Clone my_event13_fireplace material for gift_box_01..03 and attach floor clip
base_mat_idx = next(i for i, m in enumerate(hdoc['materials']) if m.get('name') == 'my_event13_fireplace')
gift_mat = copy.deepcopy(hdoc['materials'][base_mat_idx])
gift_mat['name'] = 'my_event13_fireplace_giftbox'
gift_mat.setdefault('extras', {})['BA_liquidReceiver'] = dict(floor_spec)
gift_mat_idx = len(hdoc['materials'])
hdoc['materials'].append(gift_mat)
for n in hdoc['nodes']:
    if 'mesh' in n and any(k in n.get('name', '') for k in ['gift_box_01', 'gift_box_02', 'gift_box_03']):
        for pr in hdoc['meshes'][n['mesh']]['primitives']:
            pr['material'] = gift_mat_idx
        print(f'Assigned floor-clipped giftbox material to {n["name"]}')

# 3c. Clamp negative scale overshoot on bone_gift_box_01 (and any gift bone)
hanim = hdoc['animations'][0]
for ch in hanim['channels']:
    nm = hdoc['nodes'][ch['target']['node']].get('name', '')
    if ch['target']['path'] == 'scale' and 'bone_gift_' in nm:
        s = hanim['samplers'][ch['sampler']]
        vs = read_accessor(hdoc, hdata, s['output'])
        if any(min(v) < 0.001 for v in vs):
            clamped = [[max(0.001, c) for c in v] for v in vs]
            s['output'] = append_accessor(hdoc, hdata, clamped, 'VEC3')
            print(f'Clamped negative scale overshoot on {nm}')

save(hanae_path, hdoc, compact(hdoc, hdata))
print('Saved fixed hanae_christmas/f207308_0.glb')
