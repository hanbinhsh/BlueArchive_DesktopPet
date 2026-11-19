"""Resolve all Field-Cafe standalone prefab timelines (Field833, Field843, Field_Ex2) for hina, hina_dress, seia, and np0283."""
import json
from pathlib import Path
import UnityPy
from UnityPy.classes import PPtr

R = Path(__file__).resolve().parents[1]
W = R / '.assets'

TARGET_PREFABS = {
    # hina (original)
    'field_833_common_bookshelf_01': 'hina',
    'Prop_Field_833_Zone06_Cat': 'hina',
    'Field_05_piano_01': 'hina',
    # hina_dress
    'field_833_common_table_04': 'hina_dress',
    # seia
    'Prop_Field_843_Zone11_GymBall': 'seia',
    'Prop_Field_843_Zone01_Mic': 'seia',
    'Prop_Field_843_Zone05_Cabinet': 'seia',
    'Prop_Field_843_Zone07_VendingMachine': 'seia',
    'Field_843_Common_RiosBot': 'seia',
    # np0283
    'Prop_Field_Ex2_Zone02_Cat': 'np0283',
    'Prop_Field_Ex2_Zone02_bench': 'np0283',
}

bundles = [p for p in (W / 'selected').glob('*.bundle') if any(k in p.name for k in [
    'field-cafe-',
    'field-props-',
    'field-effect-',
    'field-character-',
    'field-characters-',
    'field-player-',
]) and 'audio' not in p.name]
print(f'Loading {len(bundles)} field bundles...')
env = UnityPy.load(*map(str, bundles))

def pointer(owner, p):
    if not p or not p.get('m_PathID'):
        return None
    return PPtr(m_FileID=p['m_FileID'], m_PathID=p['m_PathID'], assetsfile=owner.assets_file).deref()

def go_path(go):
    names = [go.m_Name]
    tr = next((c.component.read() for c in go.m_Component if c.component.deref().type.name == 'Transform'), None)
    while tr and tr.m_Father.m_PathID:
        tr = tr.m_Father.read()
        names.insert(0, tr.m_GameObject.read().m_Name)
    return '/'.join(names)

out = []
for obj in env.objects:
    if obj.type.name != 'PlayableDirector':
        continue
    director = obj.read()
    go = director.m_GameObject.read()
    p = go_path(go)
    root_name = p.split('/')[0]
    if root_name not in TARGET_PREFABS:
        continue
    if not director.m_PlayableAsset.m_PathID:
        continue
    root = director.m_PlayableAsset.deref()
    timeline = root.read_typetree()
    bindings = {}
    for item in director.m_SceneBindings:
        if item.value.m_PathID:
            v = item.value.read()
            bindings[item.key.m_PathID] = go_path(v.m_GameObject.read()) if hasattr(v, 'm_GameObject') else getattr(v, 'm_Name', '')
    tracks = []
    def walk_track(o, parents):
        if o is None:
            return
        d = o.read_typetree()
        name = d.get('m_Name', '')
        clips = []
        for c in d.get('m_Clips', []):
            if not c.get('m_Asset', {}).get('m_PathID'):
                continue
            a = pointer(o, c['m_Asset'])
            if a is None:
                continue
            v = a.read_typetree()
            if v.get('m_Clip', {}).get('m_PathID'):
                cl = pointer(a, v['m_Clip'])
                clips.append({
                    'type': 'AnimationPlayableAsset',
                    'name': cl.read().m_Name if cl else '?',
                    'start': c['m_Start'],
                    'duration': c['m_Duration'],
                    'clipIn': c['m_ClipIn'],
                    'speed': c['m_TimeScale'],
                    'offset': v.get('m_Position'),
                    'rotation': v.get('m_EulerAngles'),
                    'asset': v,
                })
            elif 'sourceGameObject' in v or 'prefabGameObject' in v:
                clips.append({
                    'type': 'ControlPlayableAsset',
                    'displayName': c.get('m_DisplayName', ''),
                    'start': c['m_Start'],
                    'duration': c['m_Duration'],
                })
            else:
                clips.append({
                    'type': a.type.name,
                    'displayName': c.get('m_DisplayName', ''),
                    'start': c['m_Start'],
                    'duration': c['m_Duration'],
                })
        if clips:
            tracks.append({
                'parents': parents,
                'name': name,
                'binding': bindings.get(o.path_id),
                'position': d.get('m_Position'),
                'rotation': d.get('m_EulerAngles'),
                'clips': clips,
            })
        for child in d.get('m_Children', []):
            walk_track(pointer(o, child), parents + [name])
    for t in timeline.get('m_Tracks', []):
        walk_track(pointer(root, t), [])
    out.append({
        'character': TARGET_PREFABS[root_name],
        'prefab': root_name,
        'directorPath': p,
        'collection': obj.assets_file.name,
        'pathId': obj.path_id,
        'timeline': timeline['m_Name'],
        'tracks': tracks,
    })

out.sort(key=lambda r: (r['character'], r['prefab'], r['directorPath'], r['timeline']))
(W / 'field-cafe-timelines.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf8')
print(f'Resolved {len(out)} Field-Cafe directors:')
for r in out:
    print(f"\n[{r['character']}] {r['prefab']} :: {r['directorPath']} -> {r['timeline']}")
    for t in r['tracks']:
        summary = [(c.get('name') or c.get('displayName'), c['type'], round(c['start'], 3), round(c['duration'], 3)) for c in t['clips']]
        print(f"    track={t['name']!r} binding={t['binding']!r} clips={summary}")
