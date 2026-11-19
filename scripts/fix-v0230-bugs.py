"""Apply v0.2.30 fixes: wall_04 rain/lights/dual, stencil portals (divingpool/gunrange/siblings), planar mirror (saori_dress), shizuko/nodoka FX reparenting, and Wave 20 real yaw field."""
import copy, json, math, os, pathlib, struct, subprocess, sys
import numpy as np
import UnityPy
from UnityPy.export.MeshExporter import MeshHandler
from glb import load, save, append_accessor, compact

R = pathlib.Path(__file__).resolve().parents[1]
W = R / '.assets'
PY = sys.executable

def read_json(p): return json.loads(p.read_text('utf8'))
def write_json(p, v): p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n', 'utf8')

# ==============================================================================
# 1. MISAKI & SAORI LANDING WINDOW (my_cafe_01_b_wall_04):
#    - Add dual interaction profile (MakeTrack_10041_10048) for misaki & saori
#    - Rebuild solo + dual GLBs & attach FX_My_Cafe_Wall_01 (rain + night glass + blue cones)
#    - Fix FX_MAT_Wall_Stretch_Line_01 (opaque yellow cones -> soft transparent warm glow)
# ==============================================================================
profiles_path = W / 'furniture-profiles.json'
profiles = read_json(profiles_path)
m_solo = next(p for p in profiles if p['character'] == 'misaki' and p['icon'] == 'my_cafe_01_b_wall_04' and p['group'] == 'MakeTrack_10041')
s_solo = next(p for p in profiles if p['character'] == 'saori' and p['icon'] == 'my_cafe_01_b_wall_04' and p['group'] == 'MakeTrack_10048')

# Add dual profiles if not present
def ensure_dual(base, partner_id, group_name):
    if any(p['character'] == base['character'] and p['icon'] == base['icon'] and p['group'] == group_name for p in profiles):
        return
    dup = copy.deepcopy(base)
    dup['group'] = group_name
    dup['variant'] = 2
    dup['participants'] = ['10041', '10048']
    dup['studentTrack']['parents'] = [group_name]
    profiles.append(dup)

ensure_dual(m_solo, '10048', 'MakeTrack_10041_10048')
ensure_dual(s_solo, '10041', 'MakeTrack_10041_10048')
write_json(profiles_path, profiles)

# Update wall04 cafe-fx source.json to also include control for MakeTrack_10041_10048
wall_fx_src_path = W / 'cafe-fx-wall04/source.json'
wall_fx_src = read_json(wall_fx_src_path)
for tl in wall_fx_src['timelines']:
    if tl['icon'] == 'my_cafe_01_b_wall_04':
        if not any('MakeTrack_10041_10048' in c['parents'] for c in tl['controls']):
            dual_ctrl = copy.deepcopy(tl['controls'][0])
            dual_ctrl['parents'] = ['MakeTrack_10041_10048']
            tl['controls'].append(dual_ctrl)
write_json(wall_fx_src_path, wall_fx_src)

# Rebuild misaki & saori furniture GLBs (solo f1108_0 + dual f1108_1)
env_prep = {**os.environ, 'BA_CHARACTER_OUTPUT': str(R / 'characters')}
subprocess.run([PY, str(R / 'scripts/prepare-furniture.py'), 'misaki', 'saori'], env=env_prep, check=True)

# Clean old cafe-fx base backups for misaki/saori so prepare-cafe-effects uses freshly built solo+dual GLBs
for ch in ['misaki', 'saori']:
    base_dir = W / 'cafe-fx/base' / ch
    if base_dir.exists():
        for f in base_dir.glob('f1108_*.glb'):
            f.unlink()

env_fx = {**os.environ, 'BA_FX_SOURCE': str(W / 'cafe-fx-wall04'), 'BA_FX_STAGE': str(R / 'characters')}
subprocess.run([PY, str(R / 'scripts/prepare-cafe-effects.py'), 'misaki', 'saori'], env=env_fx, check=True)

# Fix wall_04 lamp cone transparency (FX_MAT_Wall_Stretch_Line_01) & ensure Light_01..03 (FX_MAT_Gra_W_30) soft transparent
for ch in ['misaki', 'saori']:
    for fname in ['f1108_0.glb', 'f1108_1.glb']:
        gp = R / 'characters' / ch / fname
        if not gp.exists():
            continue
        d, b = load(gp)
        for m in d.get('materials', []):
            mn = m.get('name', '')
            if mn == 'FX_MAT_Wall_Stretch_Line_01':
                m['alphaMode'] = 'BLEND'
                m['doubleSided'] = True
                m.setdefault('pbrMetallicRoughness', {})['baseColorFactor'] = [0.78, 0.88, 1.0, 0.14]
                m.setdefault('extras', {})['BA_depthWrite'] = False
                m['extras']['BA_renderOrder'] = 12
            elif m.get('extras', {}).get('BA_cafeParticle', {}).get('material', {}).get('name') == 'FX_MAT_Gra_W_30':
                m['alphaMode'] = 'BLEND'
                m['doubleSided'] = True
                m['extras']['BA_depthWrite'] = False
        save(gp, d, b)
        print(f'Fixed wall_04 materials on {ch}/{fname}')

# ==============================================================================
# 2. STENCIL PORTALS: kokoro/kotone divingpool, kirino gunrange, + ALL 5 siblings
# ==============================================================================
stencil_targets = sorted((R / 'characters').glob('*/f*.glb'))
for gp in stencil_targets:
    d, b = load(gp)
    mats = d.get('materials', [])
    has_hole7 = any(m.get('extras', {}).get('BA_stencil', {}).get('mode') == 'mask' and m['extras']['BA_stencil'].get('ref') == 7 for m in mats)
    if not has_hole7:
        continue
    changed = False
    for m in mats:
        st = m.get('extras', {}).get('BA_stencil')
        if st and st.get('mode') == 'not-equal' and st.get('ref') == 4:
            st['mode'] = 'equal'
            st['ref'] = 7
            changed = True
    # Clip interior particles on divingpool and gunrange to stencil == 7
    if gp.parent.name in ('kokoro', 'kotone') and gp.name.startswith('f211314_'):
        for m in mats:
            cp = m.get('extras', {}).get('BA_cafeParticle')
            if cp:
                src = cp.get('sourceName', '')
                # Keep above-water emotion icons unclipped; clip all underwater bubbles/caustics/glows
                if 'Emotion_01' not in src and 'Emotion_02' not in src:
                    m['extras']['BA_clipStencil'] = 7
                    changed = True
            elif any(k in m.get('name', '') for k in ['CH0368_', 'CH0369_']) and 'Halo' not in m.get('name', ''):
                # Prevent swimming characters inside the underwater tube (Y < -1.70) from showing below frame
                m.setdefault('extras', {})['BA_liquidReceiver'] = {
                    'node': 'furniture_0_my_event095_divingpool',
                    'normal': [0, 1, 0],
                    'constant': 1.70,
                }
                changed = True
    elif gp.parent.name == 'kirino' and gp.name == 'f211304_0.glb':
        for m in mats:
            ex = m.get('extras', {})
            if ex.get('BA_cafeParticle') or ex.get('BA_cafeTrail'):
                ex['BA_clipStencil'] = 7
                changed = True
    if changed:
        save(gp, d, b)
        print(f'Updated stencil portal clipping on {gp.parent.name}/{gp.name}')

# ==============================================================================
# 3. SAORI DRESS PLANAR MIRROR (my_event078_mirror -> saori_dress/f210366_0.glb)
# ==============================================================================
idx = read_json(W / 'furniture-index.json')
m_files = [p for p in (W / 'selected').glob('*.bundle') if 'event078_mirror' in p.name.lower() and 'audio' not in p.name.lower()]
m_files.append(W / 'selected' / idx['prefabs']['my_event078_mirror']['bundle'])
menv = UnityPy.load(*map(str, set(m_files)))
mirror_go = next(o.read() for o in menv.objects if o.type.name == 'GameObject' and o.read().m_Name == 'Mirror_RT')
mt = next(c.component.read() for c in mirror_go.m_Component if c.component.deref().type.name == 'Transform')
mmf = next(c.component.read() for c in mirror_go.m_Component if c.component.deref().type.name == 'MeshFilter')
umesh = mmf.m_Mesh.read()
mh = MeshHandler(umesh)
mh.process()

# Convert Unity left-handed mesh to glTF right-handed (negate X, flip triangle winding)
raw_pos = np.array(mh.m_Vertices, dtype=np.float32).reshape(-1, 3)
raw_pos[:, 0] *= -1.0
raw_uv = np.array(mh.m_UV0, dtype=np.float32).reshape(-1, 2) if mh.m_UV0 else np.zeros((len(raw_pos), 2), dtype=np.float32)
raw_tris = np.array([i for tri in mh.get_triangles() for i in tri], dtype=np.uint16).reshape(-1, 3)
# Flip winding so front face matches glTF right-handedness
raw_tris = raw_tris[:, [0, 2, 1]]

# Compute geometric normal in local space; inspect transform to verify world normal faces Saori
v0, v1, v2 = raw_pos[raw_tris[0]]
loc_n = np.cross(v1 - v0, v2 - v0)
loc_n = loc_n / (np.linalg.norm(loc_n) + 1e-12)

# Unity Transform -> glTF TRS: pos(-x, y, z), rot(x, -y, -z, w), scale(x, y, z)
mp = [-mt.m_LocalPosition.x, mt.m_LocalPosition.y, mt.m_LocalPosition.z]
mr = [mt.m_LocalRotation.x, -mt.m_LocalRotation.y, -mt.m_LocalRotation.z, mt.m_LocalRotation.w]
ms = [mt.m_LocalScale.x, mt.m_LocalScale.y, mt.m_LocalScale.z]

# Rotate loc_n by mr (quaternion [x, y, z, w]) to verify it points toward Saori!
def qrot(q, v):
    qx, qy, qz, qw = q
    u = np.array([qx, qy, qz])
    return v + 2.0 * np.cross(u, np.cross(u, v) + qw * v)

saori_gp = R / 'characters/saori_dress/f210366_0.glb'
sd, sb = load(saori_gp)
# Find Saori's approximate root/Bip001 X position vs mirror X position
root_idx = next(i for i, n in enumerate(sd['nodes']) if n.get('name') == 'furniture_0_my_event078_mirror')
# Check Bip001 translation sample at t=0
bip_x = 0.0
for ch in sd['animations'][0]['channels']:
    if sd['nodes'][ch['target']['node']].get('name') == 'Bip001' and ch['target']['path'] == 'translation':
        acc = sd['accessors'][sd['animations'][0]['samplers'][ch['sampler']]['output']]
        bv = sd['bufferViews'][acc['bufferView']]
        off = bv.get('byteOffset', 0) + acc.get('byteOffset', 0)
        bip_x = float(struct.unpack_from('<f', sb, off)[0])
        break

world_n = qrot(mr, loc_n)
to_saori = np.array([bip_x - mp[0], 0.0, 0.0])
if np.dot(world_n, to_saori) < 0:
    raw_tris = raw_tris[:, [0, 2, 1]]
    loc_n = -loc_n
    world_n = -world_n
print(f'Mirror_RT glTF pos={[round(x,3) for x in mp]} rot={[round(x,3) for x in mr]} scale={ms} world_n={world_n.round(3).tolist()} saori_x={bip_x:.3f}')

# Remove any previously attached mirror_rt_plane node
old_mirror_nodes = {i for i, n in enumerate(sd['nodes']) if n.get('name') == 'mirror_rt_plane'}
if old_mirror_nodes:
    for n in sd['nodes']:
        if 'children' in n:
            n['children'] = [c for c in n['children'] if c not in old_mirror_nodes]

pos_acc = append_accessor(sd, sb, raw_pos.tolist(), 'VEC3', 5126)
sd['accessors'][pos_acc]['min'] = raw_pos.min(axis=0).tolist()
sd['accessors'][pos_acc]['max'] = raw_pos.max(axis=0).tolist()
uv_acc = append_accessor(sd, sb, raw_uv.tolist(), 'VEC2', 5126)
idx_acc = append_accessor(sd, sb, raw_tris.flatten().tolist(), 'SCALAR', 5123)
mat_idx = len(sd['materials'])
sd['materials'].append({
    'name': 'FX_MAT_Mirror_RT_01',
    'pbrMetallicRoughness': {'baseColorFactor': [0.82, 0.86, 0.91, 1.0], 'metallicFactor': 0, 'roughnessFactor': 1},
    'extensions': {'KHR_materials_unlit': {}},
    'extras': {'BA_mirrorSurface': {'tint': [0.48, 0.56, 0.68], 'reflectivity': 0.95, 'normal': loc_n.tolist()}},
})
mesh_idx = len(sd['meshes'])
sd['meshes'].append({
    'name': 'FX_MESH_Mirror_Plane',
    'primitives': [{'attributes': {'POSITION': pos_acc, 'TEXCOORD_0': uv_acc}, 'indices': idx_acc, 'material': mat_idx}],
})
node_idx = len(sd['nodes'])
sd['nodes'].append({
    'name': 'mirror_rt_plane',
    'mesh': mesh_idx,
    'translation': [mp[0] + float(world_n[0]) * 0.006, mp[1], mp[2]],
    'rotation': mr,
    'scale': ms,
})
sd['nodes'][root_idx].setdefault('children', []).append(node_idx)
sb = compact(sd, sb)
save(saori_gp, sd, sb)
print('Attached live PlanarMirror surface to saori_dress/f210366_0.glb')

# ==============================================================================
# 4. REPARENT Z-UP FX ON shizuko/f203302_0.glb & nodoka_onsen/f6201_0.glb
# ==============================================================================
def reparent_fx(glb_path, from_name, to_name, fx_prefixes):
    gd, gb = load(glb_path)
    src_i = next(i for i, n in enumerate(gd['nodes']) if n.get('name') == from_name)
    dst_i = next(i for i, n in enumerate(gd['nodes']) if n.get('name') == to_name)
    moved = []
    new_children = []
    for ci in gd['nodes'][src_i].get('children', []):
        cname = gd['nodes'][ci].get('name', '')
        if any(p in cname for p in fx_prefixes):
            gd['nodes'][dst_i].setdefault('children', []).append(ci)
            moved.append(cname)
        else:
            new_children.append(ci)
    if moved:
        gd['nodes'][src_i]['children'] = new_children
        save(glb_path, gd, gb)
        print(f'Reparented {len(moved)} FX nodes in {glb_path.parent.name}/{glb_path.name} -> {to_name}: {moved}')

reparent_fx(
    R / 'characters/shizuko/f203302_0.glb',
    'furniture_0_my_event06_pocha',
    'furniture_24_my_event06_pocha_0',
    ['FX_my_event06_pocha_Emotion', 'FX_my_event06_pocha_Emotion_Speak', 'FX_my_event06_pocha_Emotion_02'],
)
reparent_fx(
    R / 'characters/nodoka_onsen/f6201_0.glb',
    'furniture_0_my_hotsprings_01_table_01',
    'furniture_5_my_hotsprings_01_table_01_0',
    ['FX_my_hotsprings_01_table_01_Emotion'],
)

# ==============================================================================
# 5. FIX ALL WAVE 20 REAL `yaw` VALUES (replacing broken `viewYaw`)
# ==============================================================================
wave20_yaws = {
    ('misaki', 'f1108_0'): 1.570796,           # facing window front-on
    ('misaki', 'f1108_1'): 1.570796,           # dual Saori & Misaki facing window front-on
    ('saori', 'f1108_0'): 1.570796,            # facing window front-on
    ('saori', 'f1108_1'): 1.570796,            # dual Saori & Misaki facing window front-on
    ('shokuhou_misaki', 'f210323_0'): 2.356194,
    ('misaki_swimsuit', 'f17105_0'): 2.356194,
    ('akari_newyear', 'f210334_0'): 2.356194,
    ('ayane', 'f11206_0'): 0.785398,
    ('ayane_swimsuit', 'f4103_0'): 0.785398,
    ('kokoro', 'f211314_0'): 1.570796,         # diving pool straight-on facing screen
    ('kokoro', 'f211314_1'): 1.570796,
    ('kotone', 'f211314_0'): 1.570796,
    ('kotone', 'f211314_1'): 1.570796,
    ('izumi_newyear', 'f210361_0'): 0.785398,
    ('saori_swimsuit', 'f17304_0'): 2.356194,
    ('saori_dress', 'f210366_0'): 2.356194,    # looking past Saori straight into live mirror!
    ('shizuko', 'f203302_0'): 0.785398,        # front-facing Shizuko at 百夜堂 stall!
    ('shizuko_swimsuit', 'f9302_0'): 5.497787, # front-facing Shizuko Swimsuit at shaved ice bar!
    ('tsukuyo', 'f4106_0'): 0.65,              # matches Image 5 (3/4 right peeking between leaves)
    ('tsukuyo_dress', 'f210389_0'): 0.785398,  # matches Image 6 (curved curtain + dress rack front-left + spotlight right)
}
yaw_file = R / 'scripts/furniture-character-view-yaw.json'
yaw_map = read_json(yaw_file)
for p in sorted((R / 'characters').glob('*/character.json')):
    ch = p.parent.name
    c = read_json(p)
    changed = False
    for f in c.get('furniture', []):
        if 'viewYaw' in f:
            del f['viewYaw']
            changed = True
        if (ch, f['id']) in wave20_yaws:
            f['yaw'] = wave20_yaws[(ch, f['id'])]
            yaw_map.setdefault(ch, {})[f['id']] = round(f['yaw'] - 2.356194490192345, 6)
            changed = True
    if changed:
        write_json(p, c)
write_json(yaw_file, dict(sorted(yaw_map.items())))
print('Cleaned up viewYaw and applied real yaw values across all Wave 20 furniture.')
