"""Audit materials, alpha modes, stencils, and Z-up FX containers on all staged Wave 21 GLBs."""
import io, pathlib
from PIL import Image
from glb import load

stage = pathlib.Path('.assets/wave21-final')
seen = set()
flagged = []
for glb_p in sorted(stage.rglob('*.glb')):
    d, b = load(glb_p)
    for m in d.get('materials', []):
        am = m.get('alphaMode', 'OPAQUE')
        ac = m.get('alphaCutoff', 0.5)
        pbr = m.get('pbrMetallicRoughness', {})
        bf = pbr.get('baseColorFactor', [1, 1, 1, 1])
        tex_idx = pbr.get('baseColorTexture', {}).get('index')
        tex_alpha = None
        if tex_idx is not None and am in ('MASK', 'BLEND'):
            img_idx = d['textures'][tex_idx]['source']
            bv = d['bufferViews'][d['images'][img_idx]['bufferView']]
            raw = b[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]
            im = Image.open(io.BytesIO(raw)).convert('RGBA')
            tex_alpha = im.getextrema()[3]
        mname = m.get('name') or ''
        key = (glb_p.parent.name, mname, am, round(ac, 3), round(bf[3], 3), tex_alpha)
        if key in seen:
            continue
        seen.add(key)
        flag = ''
        if am == 'MASK' and tex_alpha and tex_alpha[1] < ac * 255:
            flag = '!!MASK_ALL_DISCARDED!!'
        elif am == 'BLEND' and tex_alpha == (255, 255) and bf[3] >= 0.99 and not m.get('extras', {}).get('BA_cafeParticle') and not m.get('extras', {}).get('BA_waterSurface'):
            flag = '!!BLEND_OPAQUE_ALPHA!!'
        if m.get('extras', {}).get('BA_stencil'):
            print(f'  STENCIL {glb_p.parent.name:18s} {glb_p.name:14s} mat={mname:40s} {m["extras"]["BA_stencil"]}')
        if flag or (am != 'OPAQUE' and any(k in mname.lower() for k in ['glass', 'galss', 'water', 'cup', 'drink', 'window', 'bottle', 'liquid', 'ice', 'mirror', 'pool'])):
            line = f'{glb_p.parent.name:18s} {glb_p.name:16s} mat={mname:42s} {am:5s} cut={ac:.2f} bfA={bf[3]:.2f} texA={tex_alpha} {flag}'
            print(line)
            if flag:
                flagged.append(line)
print(f'\nTotal flagged material issues: {len(flagged)}')
