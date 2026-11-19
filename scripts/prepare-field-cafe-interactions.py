"""Compose all 34 Field-Cafe exploration character/furniture interactions for hina, hina_dress, seia, and np0283."""
import ast, copy, io, json, math, re, sys
from pathlib import Path
import numpy as np
import UnityPy
from glb import load, save, append_view, append_accessor, read_accessor, compact
from furniture_geometry import restore_geometry
from mouth_events import mouth_events
from furniture_fx import adapt_masked_fx
from furniture_water_fx import adapt_water_fx
from furniture_tint import adapt_simple_tint
from prop_materials import adapt_prop_material
from timeline_visibility import boolean_curves

R = Path(__file__).resolve().parents[1]
W = R / '.assets'

# Reuse the reviewed functions from prepare-furniture.py without running its main loop.
names = {'renderers', 'adapt_furniture', 'merge', 'interpolate', 'bake', 'timeline_metadata'}
module = ast.parse((R / 'scripts/prepare-furniture.py').read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in module.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), 'prepare-furniture-functions', 'exec'))

# Load only the Field-Cafe prefab bundles and their transitive CAB dependencies.
cabs = json.loads((W / 'cab-index.json').read_text('utf8'))['cabs']
bundle_names = set()
def collect_deps(bname):
    if bname in bundle_names:
        return
    p = W / 'selected' / bname
    if not p.exists():
        return
    bundle_names.add(bname)
    env0 = UnityPy.load(str(p))
    for asset in env0.files.values():
        for f in getattr(asset, 'files', {}).values():
            for ref in getattr(f, 'externals', []):
                cab = ref.path.split('/')[-1].lower()
                if cab in cabs:
                    dep = cabs[cab][1]
                    if any(k in dep.lower() for k in ['monoscripts', 'audio']):
                        continue
                    collect_deps(dep)

for root_b in [
    'field-cafe-_mxload-prefabs-2025-07-02_assets_all_9108106.bundle',
    'field-cafe-_mxload-prefabs-2026-04-27_assets_all_1871240492.bundle',
]:
    collect_deps(root_b)
for extra_b in (W / 'selected').glob('*.bundle'):
    if any(k in extra_b.name.lower() for k in ['riosbot', 'avantgarde', 'avantguard', 'shader']):
        bundle_names.add(extra_b.name)

print(f'Loading {len(bundle_names)} Field-Cafe bundles for material/mesh adaptation...', flush=True)
source_files = [str(W / 'selected' / n) for n in sorted(bundle_names)]
builtins = W / 'jp/windows/.state/runtime/1.73.459696/Package/Extracted/assets/bin/Data/unity default resources'
if builtins.exists():
    source_files.append(str(builtins))
env = UnityPy.load(*source_files)

PREFAB_NAMES = {
    'field_833_common_bookshelf_01',
    'Prop_Field_833_Zone06_Cat',
    'Field_05_piano_01',
    'field_833_common_table_04',
    'Prop_Field_843_Zone11_GymBall',
    'Prop_Field_843_Zone01_Mic',
    'Prop_Field_843_Zone05_Cabinet',
    'Prop_Field_843_Zone07_VendingMachine',
    'Field_843_Common_RiosBot',
    'Prop_Field_Ex2_Zone02_Cat',
    'Prop_Field_Ex2_Zone02_bench',
}

prefabs_map = {}
for o in env.objects:
    if o.type.name != 'GameObject':
        continue
    go = o.read()
    if go.m_Name not in PREFAB_NAMES:
        continue
    tr = next((c.component.read() for c in go.m_Component if c.component.deref().type.name == 'Transform'), None)
    if tr and not tr.m_Father.m_PathID:
        # Prefer the concrete prefab inside field-cafe-_mxload-prefabs-*
        src_name = Path(o.assets_file.parent.name).name.lower()
        if go.m_Name not in prefabs_map or src_name.startswith('field-cafe-_mxload-prefabs-'):
            prefabs_map[go.m_Name] = go

missing_p = PREFAB_NAMES - set(prefabs_map)
assert not missing_p, f'Missing Field-Cafe prefabs: {missing_p}'

def prefab(name):
    return prefabs_map[name]

# Map each timeline to its clean id & Chinese label
TIMELINE_LABELS = {
    # hina
    ('hina', 'field_833_common_bookshelf_01_Start'): ('field_bookshelf_start', '书架 · 取书'),
    ('hina', 'field_833_common_bookshelf_01_Ing'): ('field_bookshelf_ing', '书架 · 阅览'),
    ('hina', 'field_833_common_bookshelf_01_End'): ('field_bookshelf_end', '书架 · 归放'),
    ('hina', 'Prop_Field_833_Zone06_Cat_Start'): ('field_cat_start', '街角猫咪 · 靠近'),
    ('hina', 'Prop_Field_833_Zone06_Cat_Ing'): ('field_cat_ing', '街角猫咪 · 抚摸'),
    ('hina', 'Prop_Field_833_Zone06_Cat_End'): ('field_cat_end', '街角猫咪 · 告别'),
    ('hina', 'Field_05_piano_01_Ing'): ('field_piano_ing', '钢琴 · 演奏'),
    # hina_dress
    ('hina_dress', 'field_833_common_table_04_Start'): ('field_table_start', '宴会餐桌 · 就座'),
    ('hina_dress', 'field_833_common_table_04_Ing'): ('field_table_ing', '宴会餐桌 · 休憩'),
    ('hina_dress', 'field_833_common_table_04_End'): ('field_table_end', '宴会餐桌 · 离席'),
    # seia
    ('seia', 'Prop_Field_843_Zone11_GymBall_Start'): ('field_gymball_start', '健身球 · 坐上'),
    ('seia', 'Prop_Field_843_Zone11_GymBall_Ing'): ('field_gymball_ing', '健身球 · 弹跳'),
    ('seia', 'Prop_Field_843_Zone11_GymBall_End'): ('field_gymball_end', '健身球 · 下来'),
    ('seia', 'Prop_Field_843_Zone01_Mic_Start'): ('field_mic_start', '麦克风 · 上前'),
    ('seia', 'Prop_Field_843_Zone01_Mic_Ing'): ('field_mic_ing', '麦克风 · 发言'),
    ('seia', 'Prop_Field_843_Zone01_Mic_End'): ('field_mic_end', '麦克风 · 结束'),
    ('seia', 'Prop_Field_843_Zone05_Cabinet_Start'): ('field_cabinet_start', '储物柜 · 打开'),
    ('seia', 'Prop_Field_843_Zone05_Cabinet_Ing'): ('field_cabinet_ing', '储物柜 · 查看'),
    ('seia', 'Prop_Field_843_Zone05_Cabinet_End'): ('field_cabinet_end', '储物柜 · 关闭'),
    ('seia', 'Prop_Field_843_Zone07_VendingMachine_01_Start'): ('field_vending01_start', '自动贩卖机① · 操作'),
    ('seia', 'Prop_Field_843_Zone07_VendingMachine_01_Ing'): ('field_vending01_ing', '自动贩卖机① · 互动'),
    ('seia', 'Prop_Field_843_Zone07_VendingMachine_01_End'): ('field_vending01_end', '自动贩卖机① · 离开'),
    ('seia', 'Prop_Field_843_Zone07_VendingMachine_02_Start'): ('field_vending02_start', '自动贩卖机② · 操作'),
    ('seia', 'Prop_Field_843_Zone07_VendingMachine_02_Ing'): ('field_vending02_ing', '自动贩卖机② · 互动'),
    ('seia', 'Prop_Field_843_Zone07_VendingMachine_02_End'): ('field_vending02_end', '自动贩卖机② · 离开'),
    ('seia', 'Field_843_Common_RiosBot_Start'): ('field_riosbot_start', '莉音机械犬 · 启动'),
    ('seia', 'Field_843_Common_RiosBot_Ing'): ('field_riosbot_ing', '莉音机械犬 · 互动'),
    ('seia', 'Field_843_Common_RiosBot_End'): ('field_riosbot_end', '莉音机械犬 · 结束'),
    # np0283
    ('np0283', 'Prop_Field_Ex2_Zone02_Cat_NP0283_NonWeapon_01_Start'): ('field_cat_start', '街角猫咪 · 靠近'),
    ('np0283', 'Prop_Field_Ex2_Zone02_Cat_NP0283_NonWeapon_01_Idle'): ('field_cat_ing', '街角猫咪 · 抚摸'),
    ('np0283', 'Prop_Field_Ex2_Zone02_Cat_NP0283_NonWeapon_01_End'): ('field_cat_end', '街角猫咪 · 告别'),
    ('np0283', 'Prop_Field_Ex2_Zone02_bench_Start'): ('field_bench_start', '公园长椅 · 坐下'),
    ('np0283', 'Prop_Field_Ex2_Zone02_bench_Ing'): ('field_bench_ing', '公园长椅 · 休憩'),
    ('np0283', 'Prop_Field_Ex2_Zone02_bench_End'): ('field_bench_end', '公园长椅 · 起身'),
}

# Desired presentation order per character
ORDER = list(TIMELINE_LABELS.keys())

CHAR_CLIP_GLBS = {
    'hina': next((W / 'field-cafe-exported').rglob('Field_Player_Hina_Original_NonWeapon.glb')),
    'hina_dress': next((W / 'field-cafe-exported').rglob('Field_Player_CH0230_NonWeapon.glb')),
    'seia': next((W / 'field-cafe-exported').rglob('Field_Player_CH0070_NonWeapon.glb')),
    'np0283': next((W / 'exported/wave18-complete').rglob('Field_Player_NP0283_NonWeapon.glb')),
}

HIDE_WEAPONS = {
    'hina': {'Hina_Original_Weapon'},
    'hina_dress': {'CH0230_Weapon', 'CH0230_SkillProp'},
    'seia': {'CH0070_Weapon', 'CH0070_Weapon001'},
    'np0283': set(),
}

# Adapt each Field-Cafe furniture prefab once
adapted_furniture = {}
for pname in sorted(PREFAB_NAMES):
    glb_path = next((W / 'field-cafe-exported').rglob(f'{pname}.glb'))
    d, raw = load(glb_path)
    data = bytearray(raw)
    defaults = adapt_furniture(d, data, pname)
    # Strip Cinemachine virtual-camera screen-fade quads (VC_*/FX_DM/Fade*) that
    # are camera-lens overlays, not world furniture geometry.
    vc_nodes = set()
    def mark_subtree(idx):
        vc_nodes.add(idx)
        for ch in d['nodes'][idx].get('children', []):
            mark_subtree(ch)
    for idx, n in enumerate(d['nodes']):
        if n.get('name', '').startswith('VC_'):
            mark_subtree(idx)
    for idx in vc_nodes:
        n = d['nodes'][idx]
        if 'mesh' in n:
            n.pop('mesh', None)
            n.pop('skin', None)
            defaults[n.get('name', '')] = False
    # Field-Cafe props were authored for a fixed exploration camera; desktop 360 rotation
    # exposes reverse faces of single-sheet panels, shelves, and benches.
    for mat in d.get('materials', []):
        if not mat.get('extras', {}).get('BA_nonVisual'):
            mat['doubleSided'] = True
    adapted_furniture[pname] = (d, compact(d, data), defaults)
    print(f'Adapted furniture prefab {pname}: meshes={len(d.get("meshes",[]))} mats={len(d.get("materials",[]))} anims={len(d.get("animations",[]))}', flush=True)

timelines = json.loads((W / 'field-cafe-timelines.json').read_text('utf8'))
timeline_by_key = {(r['character'], r['timeline']): r for r in timelines}

stage_root = W / 'wave18-final'
selected_chars = set(sys.argv[1:]) if sys.argv[1:] else {'hina', 'hina_dress', 'seia', 'np0283'}

def build_node_map(src_doc, dst_doc):
    dst_by_name = {}
    for i, n in enumerate(dst_doc['nodes']):
        dst_by_name.setdefault(n.get('name', ''), []).append(i)
    nmap = {}
    for i, n in enumerate(src_doc['nodes']):
        nm = n.get('name', '')
        matches = dst_by_name.get(nm, [])
        if len(matches) == 1:
            nmap[i] = matches[0]
        elif len(matches) > 1:
            filtered = [m for m in matches if ('mesh' in n) == ('mesh' in dst_doc['nodes'][m]) and ('skin' in n) == ('skin' in dst_doc['nodes'][m])]
            if len(filtered) == 1:
                nmap[i] = filtered[0]
            else:
                nmap[i] = matches[0]
    return nmap

def bake_mapped(doc, data, source, raw, track, node_map, duration, animation):
    """Same as prepare-furniture.bake, skipping channels targeting unmapped FieldProp bones."""
    filtered_source = copy.deepcopy(source)
    for anim in filtered_source.get('animations', []):
        anim['channels'] = [c for c in anim['channels'] if c['target']['node'] in node_map]
    bake(doc, data, filtered_source, raw, track, node_map, duration, animation)

report = []
char_cache = {}

for char_key, tl_name in ORDER:
    if char_key not in selected_chars:
        continue
    row = timeline_by_key[(char_key, tl_name)]
    fid, label = TIMELINE_LABELS[(char_key, tl_name)]
    target_dir = stage_root / char_key

    if char_key not in char_cache:
        manifest = json.loads((target_dir / 'character.json').read_text('utf8'))
        # Preserve existing Cafe furniture (non-field_*), replace any previous field_*
        manifest['furniture'] = [f for f in manifest.get('furniture', []) if not f['id'].startswith('field_')]
        body, bodybin = load(target_dir / 'model.glb')
        clip_src, clip_src_bin = load(CHAR_CLIP_GLBS[char_key])
        nmap = build_node_map(clip_src, body)
        char_cache[char_key] = (manifest, body, bodybin, clip_src, clip_src_bin, nmap)
    manifest, body, bodybin, clip_src, clip_src_bin, nmap = char_cache[char_key]

    # Pick student track and furniture track(s)
    student_tracks = [
        t for t in row['tracks']
        if any(c['type'] == 'AnimationPlayableAsset' and c['name'].startswith('Field_Player_') for c in t['clips'])
    ]
    assert len(student_tracks) == 1, (char_key, tl_name, student_tracks)
    student_track = {
        'name': student_tracks[0]['name'],
        'clips': [c for c in student_tracks[0]['clips'] if c['type'] == 'AnimationPlayableAsset'],
    }

    furn_anim_tracks = [
        t for t in row['tracks']
        if any(c['type'] == 'AnimationPlayableAsset' and not c['name'].startswith('Field_Player_') and not c['name'].startswith('FX_') for c in t['clips'])
    ]
    # Ignore the 0.03s-1.33s *_Idle placeholder track when an active interaction track exists
    active_furn_tracks = [t for t in furn_anim_tracks if not t['name'].endswith('_Idle')]
    chosen_furn_tracks = active_furn_tracks or furn_anim_tracks[:1]
    furn_track = {
        'name': 'combined',
        'clips': [c for t in chosen_furn_tracks for c in t['clips'] if c['type'] == 'AnimationPlayableAsset'],
    }

    duration = max(c['start'] + c['duration'] for t in [student_track, furn_track] for c in t['clips'])

    furn, fdata, fdefaults = adapted_furniture[row['prefab']]
    doc = copy.deepcopy(body)
    data = bytearray(bodybin)
    offset = merge(doc, data, furn, fdata)

    animation = {'name': fid, 'channels': [], 'samplers': []}
    bake_mapped(doc, data, clip_src, clip_src_bin, student_track, nmap, duration, animation)
    bake(doc, data, furn, fdata, furn_track, {i: i + offset for i in range(len(furn['nodes']))}, duration, animation)
    assert len({(c['target']['node'], c['target']['path']) for c in animation['channels']}) == len(animation['channels'])

    extra = doc['scenes'][0]['extras']
    combined = timeline_metadata(clip_src, student_track, fid)
    oldvis = copy.deepcopy(extra.get('BA_pet_visibility', {'defaults': {}, 'clips': {}}))
    # Hide combat weapons for NonWeapon exploration scenes
    for i, n in enumerate(body['nodes']):
        if n.get('name') in HIDE_WEAPONS[char_key]:
            oldvis['defaults'][str(i)] = False
    # Add furniture default visibilities
    for i, n in enumerate(furn['nodes']):
        nm = n.get('name', '')
        base_nm = nm if nm in fdefaults else re.sub(r'_\d+$', '', nm)
        if base_nm in fdefaults:
            oldvis['defaults'][str(i + offset)] = fdefaults[base_nm]

    extra['BA_pet_visibility'] = {'defaults': oldvis['defaults'], 'clips': {fid: []}}
    extra['BAAD_unity_animation'] = {'schema_version': 0, 'clips': [combined]}
    extra['BA_furniture'] = {
        'id': fid,
        'sourceTimeline': tl_name,
        'sourcePrefab': row['prefab'],
        'duration': duration,
    }
    doc['animations'] = [animation]
    doc['extensionsUsed'] = list(set(doc.get('extensionsUsed', []) + ['KHR_materials_unlit']))

    filename = fid + '.glb'
    save(target_dir / filename, doc, compact(doc, data))
    mevs = mouth_events(combined, manifest['mouth']['defaultTile']) if manifest.get('mouth') else []
    manifest['furniture'].append({
        'id': fid,
        'name': label,
        'model': filename,
        'clip': fid,
        'duration': round(duration, 4),
        'mouthEvents': mevs,
        'yaw': 0,
        'note': '原版探索互动场景，人物与家具按同一时间轴同步播放。',
    })
    report.append({
        'character': char_key,
        'id': fid,
        'name': label,
        'prefab': row['prefab'],
        'sourceTimeline': tl_name,
        'duration': round(duration, 4),
        'mouthEvents': len(mevs),
    })
    print(f'  [{char_key:10s}] {fid:22s} ({label}) dur={duration:.2f}s mouth={len(mevs)}', flush=True)

# Write updated character.json for each processed character
for char_key, (manifest, *_) in char_cache.items():
    if char_key == 'np0283':
        # Remove furniture-specific clips from standalone actions (same convention as hina_pajamas)
        manifest['actions'] = [
            a for a in manifest['actions']
            if not any(k in a.get('clip', '') for k in ('Prop_Field_Ex2_Zone02_Cat', '_bench_'))
        ]
        manifest['note'] = '探索模式角色外观。猫咪互动与长椅互动的六段原版拆分动作在下方“家具互动”中播放。'
    (stage_root / char_key / 'character.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf8')
    print(f'Saved {char_key}/character.json (actions={len(manifest["actions"])}, furniture={len(manifest["furniture"])})', flush=True)

(R / 'test-results/field-cafe-composition.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
print(f'Done! Composed {len(report)} Field-Cafe interactions.')
