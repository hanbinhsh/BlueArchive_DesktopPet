"""Report bones that an animation collapses to (near) zero scale.

Blue Archive models hide parts by scaling a bone to 0.  The outline hull keys
off the skinned normal length (skinScale), so those bones matter for the
outline pass.

Usage: python scripts/audit-collapsed-bones.py <file.glb> [more.glb ...]
"""
import json
import struct
import sys


def read_glb(path):
    with open(path, 'rb') as fh:
        data = fh.read()
    magic, version, length = struct.unpack_from('<4sII', data, 0)
    assert magic == b'glTF' and version == 2, path
    offset, info = 12, {}
    while offset < length:
        size, kind = struct.unpack_from('<II', data, offset)
        payload = data[offset + 8:offset + 8 + size]
        info['json' if kind == 0x4E4F534A else 'bin'] = payload
        offset += 8 + size
    return json.loads(info['json']), info['bin']


COMPONENT = {5126: ('f', 4), 5123: ('H', 2), 5121: ('B', 1)}


def read_accessor(gltf, binary, index):
    acc = gltf['accessors'][index]
    view = gltf['bufferViews'][acc['bufferView']]
    fmt, size = COMPONENT[acc['componentType']]
    ncomp = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[acc['type']]
    start = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    stride = view.get('byteStride') or size * ncomp
    out = []
    for i in range(acc['count']):
        base = start + i * stride
        out.append(struct.unpack_from('<' + fmt * ncomp, binary, base))
    return out


def main(paths):
    for path in paths:
        gltf, binary = read_glb(path)
        nodes = gltf.get('nodes', [])
        collapsed = {}
        for anim in gltf.get('animations', []):
            for channel in anim.get('channels', []):
                target = channel['target']
                if target.get('path') != 'scale' or 'node' not in target:
                    continue
                sampler = anim['samplers'][channel['sampler']]
                values = read_accessor(gltf, binary, sampler['output'])
                if sampler.get('interpolation') == 'CUBICSPLINE':
                    values = values[1::3]  # in-tangent, value, out-tangent per key
                smallest = min(max(abs(c) for c in v) for v in values) if values else 1
                if smallest < 0.02:
                    name = nodes[target['node']].get('name', str(target['node']))
                    collapsed.setdefault((anim.get('name'), name), smallest)
        print(f'{path}: {len(gltf.get("animations", []))} animations, '
              f'{len(collapsed)} collapsed-scale channels (<0.02)')
        for (anim, node), value in sorted(collapsed.items()):
            print(f'  {anim} -> {node} scale={value:.6g}')


if __name__ == '__main__':
    main(sys.argv[1:])