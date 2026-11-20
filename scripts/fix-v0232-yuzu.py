#!/usr/bin/env python3
"""Fix all Yuzu Maid (CH0203) clipping and Genryumon Cutin prop issues:
1. Upright-box gated floor clip on CH0203_Body:
   - Raises maxHeight to 0.14 and followOffset to 0.085 so Cafe_Reaction (interact)
     never exposes the skirt during the opening jump (t=0.05..0.23, h up to 0.081).
   - Checks alignNode=bone_box_main (minScale=0.3, minUpDot=0.9, targetNode=Bip001,
     maxLateral=0.4) with fallbackConstant=10 so tipped-over box animations (Exs,
     Tactical_Start), shrunken-box animations (ST_Death, Formation_Pickup), and
     off-box animations (Exs_Cutin_Genryumon_AR/HG) never clip her skirt or feet.
2. Hide un-animated bind-pose props (bone_bullet_01, bone_duster_main, bone_box_main,
   CH0203_Box_Outline) in CH0203_Exs_Cutin_Genryumon_AR and _HG.
"""
import json
import pathlib
import struct

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_glb(path: pathlib.Path):
    data = path.read_bytes()
    jlen = struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:20 + jlen].decode('utf-8'))
    blen = struct.unpack_from('<I', data, 20 + jlen)[0]
    buf = bytearray(data[28 + jlen:28 + jlen + blen])
    return doc, buf


def save_glb(path: pathlib.Path, doc: dict, buf: bytearray):
    while len(buf) % 4:
        buf.append(0)
    doc['buffers'][0]['byteLength'] = len(buf)
    jbytes = json.dumps(doc, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    while len(jbytes) % 4:
        jbytes += b' '
    total = 12 + 8 + len(jbytes) + 8 + len(buf)
    header = struct.pack('<4sII', b'glTF', 2, total)
    jchunk = struct.pack('<II', len(jbytes), 0x4E4F534A) + jbytes
    bchunk = struct.pack('<II', len(buf), 0x004E4942) + bytes(buf)
    path.write_bytes(header + jchunk + bchunk)


def append_accessor(doc: dict, buf: bytearray, floats: list[float], acc_type: str, include_minmax=False) -> int:
    while len(buf) % 4:
        buf.append(0)
    off = len(buf)
    raw = struct.pack(f'<{len(floats)}f', *floats)
    buf.extend(raw)
    bv_idx = len(doc['bufferViews'])
    doc['bufferViews'].append({
        'buffer': 0,
        'byteOffset': off,
        'byteLength': len(raw),
    })
    comps = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[acc_type]
    count = len(floats) // comps
    acc = {
        'bufferView': bv_idx,
        'componentType': 5126,
        'count': count,
        'type': acc_type,
    }
    if include_minmax:
        acc['min'] = [min(floats[c::comps]) for c in range(comps)]
        acc['max'] = [max(floats[c::comps]) for c in range(comps)]
    idx = len(doc['accessors'])
    doc['accessors'].append(acc)
    return idx


def main():
    path = ROOT / 'characters/yuzu_maid/model.glb'
    doc, buf = load_glb(path)

    # 1. Upright-box geometric clip gate on all character materials (body + head + halo)
    gate_spec = {
        'node': 'bone_root',
        'normal': [0, 0, 1],
        'constant': -0.015,
        'gate': {
            'node': 'bone_box_b_01',
            'maxHeight': 0.14,
            'fallbackConstant': 10,
            'followOffset': 0.085,
            'alignNode': 'bone_box_main',
            'minScale': 0.3,
            'minUpDot': 0.9,
            'targetNode': 'Bip001',
            'maxLateral': 0.4,
        },
    }
    char_mats = {'CH0203_Body', 'CH0203_Face', 'CH0203_Eyebrow', 'CH0203_EyeMouth', 'CH0203_Hair', 'CH0203_Mouth', 'CH0203_Halo', 'Yuzu_Original_Weapon'}
    for m in doc['materials']:
        if m.get('name') in char_mats:
            m.setdefault('extras', {})['BA_liquidReceiver'] = gate_spec

    # 2. Hide un-animated bind-pose props in Genryumon_AR and Genryumon_HG
    nodes = doc['nodes']
    node_id = {n.get('name'): i for i, n in enumerate(nodes)}
    bullet_id = node_id['bone_bullet_01']
    duster_id = node_id['bone_duster_main']
    box_main_id = node_id['bone_box_main']
    box_mesh_id = next(i for i, n in enumerate(nodes) if n.get('name') == 'CH0203_Box_Outline' and 'mesh' in n)

    t_acc = append_accessor(doc, buf, [0.0], 'SCALAR', include_minmax=True)
    tiny_scale_acc = append_accessor(doc, buf, [0.0001, 0.0001, 0.0001], 'VEC3')
    zero_vec_acc = append_accessor(doc, buf, [0.0, 0.0, 0.0], 'VEC3')

    pv = doc['scenes'][0]['extras']['BA_pet_visibility']
    pv.pop('tracks', None)
    clips = pv.setdefault('clips', {})

    for anim in doc['animations']:
        name = anim.get('name', '')
        if 'Genryumon_' not in name:
            continue
        existing = {(ch['target']['node'], ch['target']['path']) for ch in anim['channels']}
        for nid, path_name, out_acc in [
            (bullet_id, 'scale', tiny_scale_acc),
            (bullet_id, 'translation', zero_vec_acc),
            (duster_id, 'scale', tiny_scale_acc),
            (duster_id, 'translation', zero_vec_acc),
            (box_main_id, 'scale', tiny_scale_acc),
            (box_main_id, 'translation', zero_vec_acc),
        ]:
            if (nid, path_name) in existing:
                continue
            s_idx = len(anim['samplers'])
            anim['samplers'].append({
                'input': t_acc,
                'interpolation': 'STEP',
                'output': out_acc,
            })
            anim['channels'].append({
                'sampler': s_idx,
                'target': {'node': nid, 'path': path_name},
            })
        # Also hide CH0203_Box_Outline mesh via BA_pet_visibility clips
        clip_tracks = clips.setdefault(name, [])
        if not any(tr.get('node') == box_mesh_id for tr in clip_tracks):
            clip_tracks.append({'node': box_mesh_id, 'keys': [[0.0, False]]})
        print(f'Patched {name}: hid bullet/duster/box channels + visibility clip for node {box_mesh_id}')

    # 3. Collapse 0.01-hidden bone_duster_main channels to 0.0001 so the 2mm handle
    #    never peeks as a 1px speck below the box in Cafe_Idle / Cafe_Reaction / etc.
    collapsed_duster = 0
    for anim in doc['animations']:
        for ch in anim['channels']:
            if ch['target']['node'] == duster_id and ch['target']['path'] == 'scale':
                s = anim['samplers'][ch['sampler']]
                acc = doc['accessors'][s['output']]
                bv = doc['bufferViews'][acc['bufferView']]
                off = bv.get('byteOffset', 0) + acc.get('byteOffset', 0)
                cnt = acc['count']
                vals = struct.unpack_from(f'<{cnt * 3}f', buf, off)
                if s.get('interpolation') == 'CUBICSPLINE':
                    key_vals = vals[3::9] + vals[4::9] + vals[5::9]
                else:
                    key_vals = vals
                if key_vals and max(abs(v) for v in key_vals) <= 0.015:
                    s['interpolation'] = 'STEP'
                    s['input'] = t_acc
                    s['output'] = tiny_scale_acc
                    collapsed_duster += 1
    print(f'Collapsed {collapsed_duster} hidden (0.01) bone_duster_main scale tracks to 0.0001')

    save_glb(path, doc, buf)
    print(f'Saved {path}')


if __name__ == '__main__':
    main()
