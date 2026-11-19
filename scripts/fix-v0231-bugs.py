"""Apply v0.2.31 fixes:
1. pina/f7106_0 yaw (match Bilibili front-side stove view) + kind=='add' sRGB fix in src/cafe-smoke.ts
3. reisa/f9106_0: attach Bag mesh+material on bench + export/append Emotion_01 (nose bubble) & Emotion_02 (ZZZ)
4. renge_swimsuit/f210371_0: restore all 8,450 submesh-0 triangles (complete white wire mesh grid) + front yaw
5. sena & sibling serina_christmas: fix default mouth tile & baked mouth mesh UVs
6. yukari_swimsuit/f13302_0: make pool water translucent so pastel mosaic bottom tiles & legs are visible
7. yuzu_maid/model.glb: follow box bottom height during Cafe_Reaction so skirt never peeks below box
8-11. cherino_onsen/f6203_0, fubuki_swimsuit/f210344_0, sakurako_idol/f210354_0/1 yaws + character search aliases
"""
import io, json, math, os, runpy, struct, subprocess, sys, zipfile
from pathlib import Path
import numpy as np
from PIL import Image
import UnityPy
from UnityPy.export.MeshExporter import MeshHandler

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import load, save, append_accessor
from rigid_geometry import rebuild_rigid_mesh

R = Path(__file__).resolve().parents[1]
W = R / '.assets'
PY = sys.executable

read_json = lambda p: json.loads(p.read_text('utf8'))
write_json = lambda p, v: p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n', 'utf8')

zips = {p.name: p for p in W.rglob('*.zip')}
cab_index = read_json(W / 'cab-index.json')['cabs']
fi = read_json(W / 'furniture-index.json')

def extract_bundle(pack, bname, dst_dir):
    dst_dir.mkdir(parents=True, exist_ok=True)
    out = dst_dir / Path(bname).name
    if out.exists():
        return out
    with zipfile.ZipFile(zips[pack]) as zf:
        zn = next(n for n in zf.namelist() if n.endswith(Path(bname).name))
        out.write_bytes(zf.read(zn))
    return out

def load_cab_env(cab_name):
    pack, bname = cab_index[cab_name.lower()]
    p = extract_bundle(pack, bname, W / 'v0231-bundles')
    return UnityPy.load(str(p)), p

# ==============================================================================
# ITEM 4: renge_swimsuit/f210371_0.glb — restore ALL 8,450 submesh-0 tris (wire net!)
# ==============================================================================
print('=== ITEM 4: Restoring full Unity mesh on renge_swimsuit/f210371_0.glb ===')
rg_path = R / 'characters/renge_swimsuit/f210371_0.glb'
rg_doc, rg_bin = load(rg_path)

# Load prefab + mesh + material bundles into one UnityPy env
rg_env = UnityPy.Environment()
rg_info = fi['prefabs']['my_event081_watergunstand']
rg_env.load_file(str(extract_bundle(rg_info['pack'], rg_info['bundle'], W / 'v0231-bundles')))
for ck in ['cab-495f1adff17dac91e7e072e95288cb2d', 'cab-5c81341a02c10ffbb18a6a8afde2589e']:
    pack, bname = cab_index[ck]
    rg_env.load_file(str(extract_bundle(pack, bname, W / 'v0231-bundles')))

smr = next(
    o.read() for o in rg_env.objects
    if o.type.name == 'SkinnedMeshRenderer' and o.read().m_GameObject.read().m_Name == 'my_event081_watergunstand'
)
unity_mesh = smr.m_Mesh.read()
mh = MeshHandler(unity_mesh)
mh.process()

# Build bone remap from Unity SMR m_Bones -> glTF skin joints of node 155
node_rg = next(n for n in rg_doc['nodes'] if n.get('name') == 'furniture_14_my_event081_watergunstand_0')
skin_rg = rg_doc['skins'][node_rg['skin']]
joint_by_suffix = {}
for ji, ni in enumerate(skin_rg['joints']):
    nm = rg_doc['nodes'][ni]['name']
    # Strip furniture_<num>_ prefix
    parts = nm.split('_', 2)
    short = parts[2] if len(parts) == 3 and parts[0] == 'furniture' else nm
    joint_by_suffix[short] = ji

remap = []
for bp in smr.m_Bones:
    bname = bp.read().m_GameObject.read().m_Name
    assert bname in joint_by_suffix, f'Missing bone {bname} in {list(joint_by_suffix)}'
    remap.append(joint_by_suffix[bname])

rebuild_rigid_mesh(rg_doc, rg_bin, node_rg, smr, mh, remap, weighted=True)
new_mesh = rg_doc['meshes'][node_rg['mesh']]
tri_counts = [rg_doc['accessors'][p['indices']]['count'] // 3 for p in new_mesh['primitives']]
print('  Restored renge_swimsuit rack mesh triangles per prim:', tri_counts)
assert tri_counts == [8450, 96], f'Unexpected tri counts: {tri_counts}'
save(rg_path, rg_doc, rg_bin)

# ==============================================================================
# ITEM 3: reisa/f9106_0.glb — attach Bag mesh+texture + export Emotion_01 (nose bubble) & Emotion_02 (ZZZ)
# ==============================================================================
print('\n=== ITEM 3: Restoring Bag mesh + Emotion_01/02 FX on reisa/f9106_0.glb ===')
rs_path = R / 'characters/reisa/f9106_0.glb'
rs_doc, rs_bin = load(rs_path)

# 3a. Attach Bag static mesh onto furniture_6_Bag
bag_env = UnityPy.Environment()
rs_info = fi['prefabs']['my_seahouse_01_table_02']
bag_env.load_file(str(extract_bundle(rs_info['pack'], rs_info['bundle'], W / 'v0231-bundles')))
for ck in ['cab-56f20024a33277995adaa72a825eded0', 'cab-3a06d0e0d767e2a86fd4f9eb47e3e3e6']:
    pack, bname = cab_index[ck]
    bag_env.load_file(str(extract_bundle(pack, bname, W / 'v0231-bundles')))

bag_mf = next(o.read() for o in bag_env.objects if o.type.name == 'MeshFilter' and o.read().m_GameObject.read().m_Name == 'Bag')
bag_mr = next(o.read() for o in bag_env.objects if o.type.name == 'MeshRenderer' and o.read().m_GameObject.read().m_Name == 'Bag')
bag_mat_name = bag_mr.m_Materials[0].read().m_Name
bag_mesh_u = bag_mf.m_Mesh.read()
bmh = MeshHandler(bag_mesh_u)
bmh.process()

# Match existing CH0167_Body material already embedded in reisa/f9106_0.glb!
bag_mat_idx = next((i for i, m in enumerate(rs_doc['materials']) if m.get('name') == bag_mat_name), None)
assert bag_mat_idx is not None, f'Material {bag_mat_name} not found in reisa/f9106_0.glb: {[m.get("name") for m in rs_doc["materials"]]}'
print(f'  Bag mesh verts={len(bmh.m_Vertices)} mat={bag_mat_name} (idx={bag_mat_idx})')

positions = [(-v[0], v[1], v[2]) for v in bmh.m_Vertices]
attrs = {'POSITION': append_accessor(rs_doc, rs_bin, positions, 'VEC3')}
rs_doc['accessors'][attrs['POSITION']].update(
    min=[min(v[i] for v in positions) for i in range(3)],
    max=[max(v[i] for v in positions) for i in range(3)],
)
if bmh.m_Normals:
    attrs['NORMAL'] = append_accessor(rs_doc, rs_bin, [(-v[0], v[1], v[2]) for v in bmh.m_Normals], 'VEC3')
if bmh.m_UV0:
    attrs['TEXCOORD_0'] = append_accessor(rs_doc, rs_bin, [(v[0], 1.0 - v[1]) for v in bmh.m_UV0], 'VEC2')
tris = bmh.get_triangles()[0]
idx_acc = append_accessor(rs_doc, rs_bin, [(v,) for a, b, c in tris for v in (a, c, b)], 'SCALAR', 5125)
bag_mesh_idx = len(rs_doc['meshes'])
rs_doc['meshes'].append({
    'name': 'furniture_6_Bag',
    'primitives': [{'attributes': attrs, 'indices': idx_acc, 'material': bag_mat_idx}],
})
bag_node_idx = next(i for i, n in enumerate(rs_doc['nodes']) if n.get('name') == 'furniture_6_Bag')
bag_parent_idx = next(i for i, n in enumerate(rs_doc['nodes']) if n.get('name') == 'furniture_5_CH0167_Body_Bag')
rs_doc['nodes'][bag_node_idx]['mesh'] = bag_mesh_idx

# Activate CH0167_Body_Bag & Bag & Emotion_02 in BA_pet_visibility for reisa/f9106_0!
vis = rs_doc['scenes'][0]['extras']['BA_pet_visibility']
vis['defaults'][str(bag_parent_idx)] = True
vis['defaults'][str(bag_node_idx)] = True
emo2_idx = next(i for i, n in enumerate(rs_doc['nodes']) if n.get('name') == 'furniture_7_FX_my_seahouse_01_table_02_Emotion_02')
vis['defaults'][str(emo2_idx)] = True
save(rs_path, rs_doc, rs_bin)
print('  Attached Bag mesh & enabled Bag/Emotion_02 visibility in reisa/f9106_0.glb')

# 3b. Export BOTH embedded ParticleSystems for reisa/f9106_0:
#   - FX_my_seahouse_01_table_02_Emotion_01 (on CH0167 character prefab -> nose bubble!)
#   - FX_my_seahouse_01_table_02_Emotion_02 (on my_seahouse_01_table_02 prefab -> Sleep_L ZZZ!)
reisa_fx_dir = W / 'cafe-embedded-reisa'
reisa_fx_dir.mkdir(exist_ok=True)
# Ensure seahouse table_02 bundles & CH0167 bundles are in .assets/selected so export-cafe-effects finds them
for ck in [
    'cab-4180cbb0a49e7e9750b80f2ec6b9f3cd',
    'cab-d462534f4e0963345ed2a62dd0c3f8dc',
    'cab-a30398f63bdfbf32a81bcca51e01fcde',
    'cab-7595ad70bfcc4ffef1db7980a2366371',
    'cab-56f20024a33277995adaa72a825eded0',
]:
    pack, bname = cab_index[ck]
    extract_bundle(pack, bname, W / 'selected')
extract_bundle(rs_info['pack'], rs_info['bundle'], W / 'selected')
# Also extract CH0167 prefabs/materials/textures/meshes to v0231-bundles
ch167_bundles = []
for ck, (pack, bname) in cab_index.items():
    if 'characters-ch0167-' in bname.lower() and not 'audio' in bname.lower() and not 'animation' in bname.lower():
        ch167_bundles.append(extract_bundle(pack, bname, W / 'v0231-bundles'))

os.environ['BA_FX_OUTPUT'] = str(reisa_fx_dir)
sys.argv = ['export-cafe-effects.py', 'my_seahouse_01_table_02']
v_fx = runpy.run_path(str(R / 'scripts/export-cafe-effects.py'))
env_fx = v_fx['env']
for bp in ch167_bundles:
    env_fx.load_file(str(bp))
# Also load any shared FX bundles referenced by Emotion_01 / Emotion_02 (load all external CABs recursively!)
loaded_cabs = {af.name.lower() for af in env_fx.files.values() if hasattr(af, 'name')}
for _round in range(4):
    new_cabs = []
    for af in list(env_fx.files.values()):
        for ext in getattr(af, 'externals', []):
            cn = ext.path.split('/')[-1].lower()
            if cn not in loaded_cabs and cn in cab_index:
                new_cabs.append(cn)
                loaded_cabs.add(cn)
    if not new_cabs:
        break
    for cn in new_cabs:
        pack, bname = cab_index[cn]
        p_ext = extract_bundle(pack, bname, W / 'v0231-bundles')
        env_fx.load_file(str(p_ext))

for t in v_fx['timelines']:
    t['controls'] = []
reisa_effects = {}

# Find FX_my_seahouse_01_table_02_Emotion_01 (character-embedded nose bubble) and FX_my_seahouse_01_table_02_Emotion_02 (table ZZZ)
go_emo1 = next(
    o.read() for o in env_fx.objects
    if o.type.name == 'GameObject' and o.read().m_Name == 'FX_my_seahouse_01_table_02_Emotion_01'
)
go_emo2 = next(
    o.read() for o in env_fx.objects
    if o.type.name == 'GameObject' and o.read().m_Name == 'FX_my_seahouse_01_table_02_Emotion_02'
)
reisa_effects['reisa__Emotion_01'] = v_fx['visit'](go_emo1)
reisa_effects['reisa__Emotion_02'] = v_fx['visit'](go_emo2)

tl_rs = next(t for t in v_fx['timelines'] if t['icon'] == 'my_seahouse_01_table_02')
tl_rs['controls'].append(dict(
    parents=['OnlyTrack_10068'],
    track='Native embedded FX',
    prefab='reisa__Emotion_01',
    existing=True,
    restartOnActivation=True,
    bindingResolved=True,
    binding='FX_my_seahouse_01_table_02_Emotion_01',
    start=0.033333333,
    duration=10.0,
    clipIn=0,
    speed=1,
    seed=0,
))
tl_rs['controls'].append(dict(
    parents=['OnlyTrack_10068'],
    track='Native embedded FX',
    prefab='reisa__Emotion_02',
    existing=True,
    restartOnActivation=True,
    bindingResolved=True,
    binding='FX_my_seahouse_01_table_02_Emotion_02',
    start=0.0,
    duration=10.033333333,
    clipIn=0,
    speed=1,
    seed=0,
))
write_json(reisa_fx_dir / 'source.json', dict(timelines=v_fx['timelines'], effects=reisa_effects, errors=v_fx['errors']))
print('  Exported Reisa Emotion_01 & Emotion_02 FX; errors:', v_fx['errors'])

# Run prepare-cafe-effects.py on characters/reisa ONLY (in a temp stage dir so we don't touch kasumi!)
reisa_stage = W / 'reisa-fx-stage'
import shutil
if reisa_stage.exists():
    shutil.rmtree(reisa_stage)
shutil.copytree(R / 'characters/reisa', reisa_stage / 'reisa')
env_sub = os.environ.copy()
env_sub['BA_FX_SOURCE'] = str(reisa_fx_dir)
env_sub['BA_FX_STAGE'] = str(reisa_stage)
env_sub['BA_FX_APPEND'] = '1'
subprocess.run([PY, str(R / 'scripts/prepare-cafe-effects.py'), 'reisa'], env=env_sub, check=True)
shutil.copy2(reisa_stage / 'reisa/f9106_0.glb', R / 'characters/reisa/f9106_0.glb')
print('  Appended Reisa Emotion_01 & Emotion_02 into characters/reisa/f9106_0.glb')

# ==============================================================================
# ITEM 5: sena & sibling serina_christmas — fix default mouth tile & baked mouth UVs
# ==============================================================================
print('\n=== ITEM 5: Fixing Sena & Serina Christmas default mouth tile & UVs ===')
def fix_mouth_default(ch_id, target_tile):
    cp = R / 'characters' / ch_id / 'character.json'
    c = read_json(cp)
    mat_name = c['mouth']['material']
    row = target_tile // 100
    col = target_tile % 100
    du = col / 8.0
    dv = -row / 8.0
    if c['mouth'].get('defaultTile') == target_tile and 'baseUV' not in c['mouth']:
        print(f'  {ch_id} already fixed to tile {target_tile}')
        return
    for gp in sorted((R / 'characters' / ch_id).glob('*.glb')):
        d, b = load(gp)
        mi = next((i for i, m in enumerate(d['materials']) if m.get('name') == mat_name), None)
        if mi is None:
            continue
        touched_accs = set()
        for mesh in d['meshes']:
            for pr in mesh['primitives']:
                if pr.get('material') == mi:
                    ai = pr['attributes']['TEXCOORD_0']
                    if ai in touched_accs:
                        continue
                    touched_accs.add(ai)
                    acc = d['accessors'][ai]
                    bv = d['bufferViews'][acc['bufferView']]
                    stride = bv.get('byteStride', 8)
                    base = bv.get('byteOffset', 0) + acc.get('byteOffset', 0)
                    for k in range(acc['count']):
                        u, v = struct.unpack_from('<ff', b, base + k * stride)
                        struct.pack_into('<ff', b, base + k * stride, u + du, v + dv)
        save(gp, d, b)
        print(f'  Shifted {ch_id}/{gp.name} {mat_name} UVs by ({du:+.4f}, {dv:+.4f})')
    c['mouth']['defaultTile'] = target_tile
    c['mouth'].pop('baseUV', None)
    write_json(cp, c)
    print(f'  Updated {ch_id}/character.json mouth.defaultTile -> {target_tile}')

fix_mouth_default('sena', 401)
fix_mouth_default('serina_christmas', 704)

# ==============================================================================
# ITEM 6: yukari_swimsuit/f13302_0.glb — transparent pool water revealing mosaic tiles
# ==============================================================================
print('\n=== ITEM 6: Fixing Yukari Swimsuit pool water transparency ===')
yk_path = R / 'characters/yukari_swimsuit/f13302_0.glb'
yk_doc, yk_bin = load(yk_path)
m60 = next(m for m in yk_doc['materials'] if m.get('name') == 'cafe_particle_60')
sf60 = m60['extras']['BA_smokeFx']
# Keep vibrant turquoise color while making water surface translucent (~42% opacity)
# so mosaic bottom tiles, steps, and Yukari's submerged legs show clearly underneath!
sf60['colors']['_Main_Color'][3] = 0.19
save(yk_path, yk_doc, yk_bin)
print('  Updated yukari_swimsuit/f13302_0.glb cafe_particle_60 _Main_Color.a -> 0.19')

# ==============================================================================
# ITEM 7: yuzu_maid/model.glb — skirt floor clip follows box bottom during Cafe_Reaction
# ==============================================================================
print('\n=== ITEM 7: Fixing Yuzu Maid Cafe_Reaction box-bottom skirt clip ===')
ym_path = R / 'characters/yuzu_maid/model.glb'
ym_doc, ym_bin = load(ym_path)
m_body = next(m for m in ym_doc['materials'] if m.get('name') == 'CH0203_Body')
m_body['extras']['BA_liquidReceiver'] = {
    'node': 'bone_root',
    'normal': [0, 0, 1],
    'constant': -0.015,
    'gate': {
        'node': 'bone_box_b_01',
        'maxHeight': 0.05,
        'fallbackConstant': 0.01,
        'followOffset': 0.075,
    },
}
save(ym_path, ym_doc, ym_bin)
print('  Updated yuzu_maid/model.glb CH0203_Body BA_liquidReceiver with followOffset=0.075')

# ==============================================================================
# ITEMS 1, 4, 8, 9, 11: Furniture yaw adjustments
# ==============================================================================
print('\n=== ITEMS 1, 4, 8, 9, 11: Updating furniture yaws ===')
yaw_updates = {
    'pina/f7106_0': 0.785398,              # Image 1: Pina on left facing stove grate on right
    'renge_swimsuit/f210371_0': 2.356194,  # Image 4: Renge on left in front of rack & wire net
    'cherino_onsen/f6203_0': 3.926991,     # Image 6: +90 deg so Cherino faces front when drinking
    'fubuki_swimsuit/f210344_0': 3.926991, # Image 7: +90 deg
    'sakurako_idol/f210354_0': 0.0,        # Image 8: dead straight-on (matching mari_idol & mine_idol)
    'sakurako_idol/f210354_1': 0.0,        # Image 8: dead straight-on
    'mari_idol/f210354_0': 0.0,
    'mari_idol/f210354_1': 0.0,
    'mine_idol/f210354_0': 0.0,
    'mine_idol/f210354_1': 0.0,
}
yp = R / 'scripts/furniture-character-view-yaw.json'
yd = read_json(yp)
for key, val in yaw_updates.items():
    ch, fid = key.split('/')
    cp = R / 'characters' / ch / 'character.json'
    c = read_json(cp)
    for f in c.get('furniture', []):
        if f['id'] == fid:
            f['yaw'] = val
    write_json(cp, c)
    yd[key] = val
    print(f'  {key} yaw -> {val}')
write_json(yp, yd)

# ==============================================================================
# ITEM 10: Character search aliases (玛丽娜, 玲女, 高音, plus common CN alternate names)
# ==============================================================================
print('\n=== ITEM 10: Adding character search aliases ===')
alias_map = {
    'marina': ['玛丽娜', '池仓玛丽娜'],
    'marina_qipao': ['玛丽娜', '玛丽娜 · 旗袍'],
    'reijo': ['玲女', '鹿山玲女'],
    'takane': ['高音', '高岭', '三善高音', '三善高岭'],
    'cherino': ['洁莉诺'],
    'cherino_onsen': ['洁莉诺'],
    'mika': ['未花'],
    'mika_swimsuit': ['未花'],
    'hifumi': ['日步美'],
    'hifumi_swimsuit': ['日步美'],
    'hifumi_racing': ['日步美'],
    'karin': ['卡琳'],
    'karin_bunny': ['卡琳'],
    'karin_uniform': ['卡琳'],
    'aris': ['爱莉丝'],
    'aris_maid': ['爱莉丝'],
    'aris_battle': ['爱莉丝'],
    'atsuko': ['敦子'],
    'atsuko_swimsuit': ['敦子'],
    'iroha': ['彩叶'],
    'iroha_swimsuit': ['彩叶'],
    'kazusa': ['一纱'],
    'kazusa_band': ['一纱'],
    'toki': ['季'],
    'toki_bunny': ['季'],
    'toki_battle': ['季'],
}
for ch_id, aliases in alias_map.items():
    cp = R / 'characters' / ch_id / 'character.json'
    if not cp.exists():
        continue
    c = read_json(cp)
    c['aliases'] = aliases
    write_json(cp, c)
print(f'  Added search aliases to {len(alias_map)} character manifests')
print('\nALL v0.2.31 ASSET FIXES COMPLETE!')
