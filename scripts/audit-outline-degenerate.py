"""Count triangles the outline hull would turn into a giant wedge.

ModelOutline welds area-weighted normals per position; a vertex whose welded
sum is zero gets a zero-length `smoothNormal`, so the outline vertex shader sees
skinScale == 0 for it.  A triangle that mixes such a vertex with normal ones is
the shape that painted the long black lines when the shader moved those
vertices to NDC (2,2).

Usage: python scripts/audit-outline-degenerate.py <file.glb> [...]
"""
import json
import math
import struct
import sys

CT = {5126: ('f', 4), 5123: ('H', 2), 5121: ('B', 1), 5125: ('I', 4)}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def load(path):
    data = open(path, 'rb').read()
    magic, version, length = struct.unpack_from('<4sII', data, 0)
    assert magic == b'glTF', path
    offset, chunks = 12, {}
    while offset < length:
        size, kind = struct.unpack_from('<II', data, offset)
        chunks[kind] = data[offset + 8:offset + 8 + size]
        offset += 8 + size
    return json.loads(chunks[0x4E4F534A]), chunks[0x004E4942]


def accessor(gltf, binary, index):
    acc = gltf['accessors'][index]
    view = gltf['bufferViews'][acc['bufferView']]
    fmt, size = CT[acc['componentType']]
    n = NC[acc['type']]
    stride = view.get('byteStride') or size * n
    start = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    return [struct.unpack_from('<' + fmt * n, binary, start + i * stride) for i in range(acc['count'])]


def key_of(position):
    return tuple(int(math.floor(v * 1e4 + 0.5)) for v in position)


def triangle_normals(gltf, binary, primitive):
    """-> list of (i0,i1,i2, cx,cy,cz) using local vertex indices."""
    positions = accessor(gltf, binary, primitive['attributes']['POSITION'])
    indices = accessor(gltf, binary, primitive['indices'])[:] if 'indices' in primitive else None
    order = [i[0] for i in indices] if indices else list(range(len(positions)))
    out = []
    for k in range(0, len(order) - 2, 3):
        a, b, c = order[k], order[k + 1], order[k + 2]
        pa, pb, pc = positions[a], positions[b], positions[c]
        ux, uy, uz = pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2]
        vx, vy, vz = pc[0] - pa[0], pc[1] - pa[1], pc[2] - pa[2]
        out.append((a, b, c, uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx))
    return positions, out


def audit_mesh(gltf, binary, primitive):
    positions, triangles = triangle_normals(gltf, binary, primitive)
    sums = {}
    for a, b, c, nx, ny, nz in triangles:
        for vid in (a, b, c):
            k = key_of(positions[vid])
            s = sums.setdefault(k, [0.0, 0.0, 0.0])
            s[0] += nx
            s[1] += ny
            s[2] += nz
    welded_zero = {k for k, s in sums.items() if not (s[0] or s[1] or s[2])}
    zero_vertices = sum(1 for v in positions if key_of(v) in welded_zero)
    mixed = sum(
        1 for a, b, c, *_ in triangles
        if any(key_of(positions[v]) in welded_zero for v in (a, b, c))
        and any(key_of(positions[v]) not in welded_zero for v in (a, b, c))
    )
    degenerate = sum(1 for _, _, _, nx, ny, nz in triangles if not (nx or ny or nz))
    return {
        'vertices': len(positions),
        'triangles': len(triangles),
        'zeroNormalVertices': zero_vertices,
        'degenerateTriangles': degenerate,
        'mixedTriangles': mixed,
    }


def main(paths):
    bad = 0
    for path in paths:
        gltf, binary = load(path)
        rows = []
        for mesh in gltf.get('meshes', []):
            for primitive in mesh['primitives']:
                if 'POSITION' not in primitive['attributes']:
                    continue
                info = audit_mesh(gltf, binary, primitive)
                if info['zeroNormalVertices'] or info['mixedTriangles']:
                    info['mesh'] = mesh.get('name', '')
                    rows.append(info)
        mixed = sum(r['mixedTriangles'] for r in rows)
        zero = sum(r['zeroNormalVertices'] for r in rows)
        print(f'{path}: meshes={len(gltf.get("meshes", []))} '
              f'zeroNormalVerts={zero} mixedTriangles={mixed}')
        for row in rows:
            print('   {mesh}: verts={vertices} zeroNormal={zeroNormalVertices} '
                  'degenerate={degenerateTriangles} mixed={mixedTriangles}'.format(**row))
        bad += mixed
    print(f'\ntotal mixed triangles: {bad}')


if __name__ == '__main__':
    main(sys.argv[1:])