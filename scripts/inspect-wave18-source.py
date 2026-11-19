"""Resolve original prefabs, authored basic clips, halo availability, dependencies, and renderer event audits for Wave 18 (+ Yukino & NP0283)."""
from pathlib import Path
import json, zipfile, zlib
import UnityPy

R = Path(__file__).resolve().parents[1]
W = R / '.assets'
specs = json.loads((R / 'scripts/roster-wave18.json').read_text('utf8'))
cabs = json.loads((W / 'cab-index.json').read_text('utf8'))['cabs']
catalog = json.loads((W / 'catalog.json').read_text('utf8'))
bundle_lookup = {b['Name']: (p['PackName'], b) for p in catalog['FullPatchPacks'] for b in p['BundleFiles']}

archives = {}
dep_extracted = 0
seen_bundles = set()

def ensure_deps(bundle_path):
    global dep_extracted
    if bundle_path.name in seen_bundles:
        return
    seen_bundles.add(bundle_path.name)
    env = UnityPy.load(str(bundle_path))
    for asset in list(env.files.values()):
        for f in getattr(asset, 'files', {}).values():
            for ref in getattr(f, 'externals', []):
                cab = ref.path.split('/')[-1].lower()
                if cab in cabs:
                    dep = cabs[cab][1]
                    if any(k in dep.lower() for k in ['monoscripts', 'shader', 'audio']):
                        continue
                    dest = W / 'selected' / dep
                    if not dest.exists():
                        if dep not in bundle_lookup:
                            continue
                        pack_name, binfo = bundle_lookup[dep]
                        if not (W / 'packs' / pack_name).exists():
                            continue
                        if pack_name not in archives:
                            archives[pack_name] = zipfile.ZipFile(W / 'packs' / pack_name)
                        raw = archives[pack_name].read(dep)
                        assert len(raw) == binfo['Size'] and zlib.crc32(raw) == binfo['Crc'], dep
                        dest.write_bytes(raw)
                        dep_extracted += 1
                    if dest.exists():
                        ensure_deps(dest)

for key, (prefix, _) in specs.items():
    for p in (W / 'selected').glob('*.bundle'):
        if f'{prefix.lower()}-' in p.name and not any(k in p.name for k in ['audio']):
            ensure_deps(p)

# Also ensure dependencies for Yukino, NP0283, and all Field-Cafe / Field-Character bundles
for pat in [
    'ch0171_enemy',
    'field-cafe-_mxload-prefabs-2025-07-02',
    'field-cafe-_mxload-prefabs-2026-04-27',
    'field-player-_mxload-prefabs-2026-04-27',
    'field-character-_mxload-prefabs-2026-04-27',
    'field-character-_mxload-prefabs-2025-07-02',
    'field-player-_mxload-prefabs-2025-07-02',
    'field-cafe-_mxdependency-timelines',
    'field-cafe-characteranimation',
]:
    for p in (W / 'selected').glob('*.bundle'):
        if pat in p.name and 'audio' not in p.name:
            ensure_deps(p)

for a in archives.values():
    a.close()
print(f'Dependency scan complete: extracted {dep_extracted} additional shared CAB bundles.')

choices = [
    ('idle', '待机', 'Cafe_Idle'),
    ('interact', '咖啡厅互动', 'Cafe_Reaction'),
    ('walk', '原地走路', 'Cafe_Walk'),
    ('victory', '胜利动作', 'Victory_Start'),
    ('reload', '换弹', 'Normal_Reload'),
    ('pickup', '编队提起', 'Formation_Pickup'),
]

rows = {}
profiles = {}
renderer_audit = {}

for key, (prefix, _) in specs.items():
    files = [p for p in (W / 'selected').glob('*.bundle') if prefix.lower() + '-' in p.name and 'audio' not in p.name]
    env = UnityPy.load(*map(str, files))
    row = {'roots': [], 'faceDefaults': [], 'clips': [], 'haloParents': []}
    prefab_gos = {}
    clip_events = {}
    for o in env.objects:
        if o.type.name == 'GameObject':
            go = o.read()
            t = next((c.component.read() for c in go.m_Component if c.component.deref().type.name == 'Transform'), None)
            if t and not t.m_Father.m_PathID:
                row['roots'].append(go.m_Name)
                prefab_gos[go.m_Name] = go
        elif o.type.name == 'MonoBehaviour':
            try:
                d = o.read_typetree()
                native = o.read()
                if not native.m_GameObject.m_PathID:
                    continue
                go = native.m_GameObject.read()
                if 'MouthDefaultUV' in d:
                    row['faceDefaults'].append({'root': go.m_Name, 'default': d['MouthDefaultUV'], 'fields': {k: v for k, v in d.items() if 'Mouth' in k or 'Renderer' in k}})
                if 'FollowTarget' in d and 'TargetRelativePosition' in d:
                    t = next(c.component.read() for c in go.m_Component if c.component.deref().type.name == 'Transform')
                    if t.m_Father.m_PathID:
                        row['haloParents'].append(t.m_Father.read().m_GameObject.read().m_Name)
            except Exception:
                pass
        elif o.type.name == 'AnimationClip':
            cl = o.read()
            row['clips'].append(cl.m_Name)
            tt = o.read_typetree()
            evs = [(round(e.get('time', 0), 3), e.get('functionName'), e.get('intParameter'))
                   for e in tt.get('m_Events', [])
                   if e.get('functionName') in ('AniEvt_EnableChildRenderer', 'AniEvt_DisableChildRenderer')]
            if evs:
                clip_events[cl.m_Name] = evs

    roots = {x['root'] for x in row['faceDefaults']}
    model = next((n for n in [prefix, 'Cafe_' + prefix, prefix + '_CafeOnly'] if n in roots), None)
    assert model, (key, roots, row['roots'])

    actions = []
    for a, b, suffix in choices:
        variants = [prefix + '_' + suffix]
        if a == 'pickup':
            variants.append(prefix + '_Fomation_Pickup')
        clip = next((v for v in variants if v in row['clips']), None)
        if clip:
            actions.append([a, b, clip])
    assert {'idle', 'interact'} <= {a[0] for a in actions}, (key, actions)

    profile = {'modelPrefix': model, 'prefabName': model, 'exportDirectory': 'wave18-complete', 'actions': actions}
    native = next(x for x in row['faceDefaults'] if x['root'] == model)
    if not native['fields']['MouthRenderer']['m_PathID']:
        assert native['fields']['MouthMaterialIndex'] == -1
        profile['noMouthAtlas'] = True
    if model not in row['haloParents']:
        profile['noHalo'] = True
    profiles[key] = profile
    rows[key] = row

    go = prefab_gos.get(model)
    r_names = []
    direct_children = []
    if go:
        tr = next(c.component.read() for c in go.m_Component if c.component.deref().type.name == 'Transform')
        for ch in tr.m_Children:
            direct_children.append(ch.read().m_GameObject.read().m_Name)
        def walk(g):
            t = None
            for c in g.m_Component:
                d = c.component.deref()
                if d.type.name in ('SkinnedMeshRenderer', 'MeshRenderer'):
                    r_names.append(g.m_Name)
                elif d.type.name == 'Transform':
                    t = d.read()
            if t:
                for ch in t.m_Children:
                    walk(ch.read().m_GameObject.read())
        walk(go)

    used_indices = sorted({idx for evs in clip_events.values() for _, _, idx in evs})
    if used_indices:
        renderer_audit[key] = {
            'model': model,
            'renderers': r_names,
            'directChildren': direct_children,
            'usedIndices': used_indices,
            'sampleEvents': {k: v for k, v in list(clip_events.items())[:5]},
        }
    print(f'{key:22s} model={model:24s} basic={len(actions)} halo={not profile.get("noHalo", False)} evIdx={used_indices}', flush=True)

# Add yukino and np0283 profiles too!
profiles['yukino'] = {
    'modelPrefix': 'CH0171_Enemy',
    'prefabName': 'CH0171_Enemy',
    'exportDirectory': 'wave18-complete',
    'actions': [
        ['idle', '待机', 'CH0171_Enemy_Normal_Idle'],
        ['interact', '登场动作', 'CH0171_Enemy_Appear'],
        ['walk', '移动', 'CH0171_Enemy_Move_Ing'],
        ['reload', '换弹', 'CH0171_Enemy_Normal_Reload'],
        ['public01', '普通技能', 'CH0171_Enemy_Public01'],
    ],
}
profiles['np0283'] = {
    'modelPrefix': 'Field_Player_NP0283_NonWeapon',
    'prefabName': 'Field_Player_NP0283_NonWeapon',
    'exportDirectory': 'wave18-complete',
    'actions': [
        ['idle', '待机', 'Field_Player_NP0283_NonWeapon_Normal_Idle'],
        ['interact', '思考', 'Field_Player_NP0283_NonWeapon_Normal_Idle_Think'],
        ['walk', '散步', 'Field_Player_NP0283_NonWeapon_Walk_Ing'],
        ['move', '奔跑', 'Field_Player_NP0283_NonWeapon_Move_Ing'],
        ['search', '搜寻', 'Field_Player_NP0283_NonWeapon_Search'],
        ['get_item', '拾取道具', 'Field_Player_NP0283_NonWeapon_Field_Get_Item'],
    ],
}

(R / 'test-results/wave18-original-structure.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), 'utf8')
(R / 'scripts/wave18-profiles.json').write_text(json.dumps(profiles, ensure_ascii=False, indent=2), 'utf8')
(R / 'test-results/wave18-renderer-audit.json').write_text(json.dumps(renderer_audit, ensure_ascii=False, indent=2), 'utf8')
print('\n=== RENDERER EVENT AUDIT (characters using AniEvt_*ChildRenderer) ===')
for k, v in renderer_audit.items():
    print(f"\n{k} ({v['model']}):")
    print(f"  renderers:      {list(enumerate(v['renderers']))}")
    print(f"  directChildren: {list(enumerate(v['directChildren']))}")
    print(f"  usedIndices:    {v['usedIndices']}")
    for ck, evs in v['sampleEvents'].items():
        print(f"    {ck}: {evs[:4]}")
