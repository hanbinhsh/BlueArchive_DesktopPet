"""Re-bake overlapping Unity Timeline segments on existing verified furniture GLBs.

Preserves all verified meshes, materials, textures, and embedded cafe FX while
replacing hard-cut clip seams with smoothstep / shortest-arc SLERP blending.
"""

import ast
import json
import math
import re
from pathlib import Path
import numpy as np

from glb import load, save, read_accessor, append_accessor, compact
from prop_visibility import apply_prop_visibility

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.assets'

# Reuse the exact bake() and interpolate() from prepare-furniture.py.
_tree = ast.parse((ROOT / 'scripts/prepare-furniture.py').read_text('utf8'))
_code = ast.Module(
    body=[n for n in _tree.body if isinstance(n, ast.FunctionDef) and n.name in ('bake', 'interpolate')],
    type_ignores=[],
)
_ns = {'np': np, 'math': math, 'append_accessor': append_accessor, 'read_accessor': read_accessor}
exec(compile(_code, 'prepare-furniture.py', 'exec'), _ns)
bake = _ns['bake']


def exported(name):
    export = WORK / 'furniture-exported/all'
    files = [
        p for p in export.rglob(name + '*.glb')
        if p.stat().st_size >= 20 and re.fullmatch(re.escape(name) + r'(?:_\d+)?', p.stem)
    ]
    if not files:
        raise ValueError('Export missing: ' + name)
    return load(max(files, key=lambda p: p.stat().st_mtime))


def build_node_map(target_nodes, source_nodes, prefix=None):
    if prefix is None:
        # Student root nodes appear before furniture_0_ and partner_ nodes.
        by_name = {}
        for i, n in enumerate(target_nodes):
            nm = n.get('name', '')
            if nm.startswith('furniture_') or nm.startswith('partner_') or nm.startswith('cafe_'):
                continue
            by_name.setdefault(nm, i)
        return {i: by_name[n['name']] for i, n in enumerate(source_nodes) if n.get('name') in by_name}
    else:
        # Furniture / partner nodes were prefixed as f'{prefix}{i}_{orig_name}'
        mapping = {}
        for ti, n in enumerate(target_nodes):
            nm = n.get('name', '')
            if nm.startswith(prefix):
                rest = nm[len(prefix):]
                idx_str, _, _ = rest.partition('_')
                if idx_str.isdigit():
                    mapping[int(idx_str)] = ti
        return mapping


def repair_sandbath(source_root, output_root):
    all_profiles = json.loads((WORK / 'furniture-profiles.json').read_text('utf8'))
    targets = [
        ('iroha_swimsuit', 'f211311_1.glb', 'RequiredTrack_10148_20060'),
        ('ibuki_swimsuit', 'f211311_1.glb', 'RequiredTrack_10148_20060'),
        ('iroha_swimsuit', 'f211311_0.glb', 'MakeTrack_10148'),
        ('ibuki_swimsuit', 'f211311_0.glb', 'MakeTrack_20060'),
    ]
    cache = {}
    def get_exported(name):
        if name not in cache:
            cache[name] = exported(name)
        return cache[name]

    for char, filename, group in targets:
        profile = next(
            p for p in all_profiles
            if p['character'] == char and p['icon'] == 'my_event094_sandbath' and p['group'] == group
        )
        doc, binary = load(source_root / char / filename)
        data = bytearray(binary)
        old_anim = doc['animations'][0]
        clip_name = old_anim['name']
        duration = max(
            c['start'] + c['duration']
            for t in [profile['studentTrack']] + profile['furnitureTracks']
            for c in t['clips']
        )
        new_anim = {'name': clip_name, 'channels': [], 'samplers': []}

        body_doc, body_raw = get_exported(profile['root'])
        s_map = build_node_map(doc['nodes'], body_doc['nodes'], prefix=None)
        bake(doc, data, body_doc, body_raw, profile['studentTrack'], s_map, duration, new_anim)

        furn_doc, furn_raw = get_exported(profile['icon'])
        f_map = build_node_map(doc['nodes'], furn_doc['nodes'], prefix='furniture_')
        for ft in profile['furnitureTracks']:
            bake(doc, data, furn_doc, furn_raw, ft, f_map, duration, new_anim)

        # Partner track if dual sandbath
        for student in profile.get('participants', []):
            if profile['studentTrack']['name'].split('_')[0] == student:
                continue
            partner = next(
                p for p in all_profiles
                if p['icon'] == profile['icon'] and p['group'] == profile['group'] and p['studentTrack']['name'] == student
            )
            p_doc, p_raw = get_exported(partner['root'])
            p_prefix = f"partner_{partner['character']}_"
            p_map = build_node_map(doc['nodes'], p_doc['nodes'], prefix=p_prefix)
            bake(doc, data, p_doc, p_raw, partner['studentTrack'], p_map, duration, new_anim)

        assert len(new_anim['channels']) == len(old_anim['channels']), (
            f"{char}/{filename}: channel count mismatch {len(new_anim['channels'])} vs {len(old_anim['channels'])}"
        )
        old_targets = {(c['target']['node'], c['target']['path']) for c in old_anim['channels']}
        new_targets = {(c['target']['node'], c['target']['path']) for c in new_anim['channels']}
        assert old_targets == new_targets, f"{char}/{filename}: target mismatch"

        doc['animations'] = [new_anim]
        dest = output_root / char
        dest.mkdir(parents=True, exist_ok=True)
        save(dest / filename, doc, compact(doc, data))
        print(f'Re-baked overlap blends: {char}/{filename} ({len(new_anim["channels"])} channels)')


def repair_shigure_bathtub(source_root, output_root):
    doc, binary = load(source_root / 'shigure_onsen' / 'f6301_0.glb')
    apply_prop_visibility(doc, 'shigure_onsen', 'my_hotsprings_01_woodenbathtub_CH0123')
    dest = output_root / 'shigure_onsen'
    dest.mkdir(parents=True, exist_ok=True)
    save(dest / 'f6301_0.glb', doc, binary)
    print('Updated visibility: shigure_onsen/f6301_0.glb')


if __name__ == '__main__':
    out = WORK / 'repair046'
    repair_shigure_bathtub(ROOT / 'characters', out)
    repair_sandbath(ROOT / 'characters', out)
