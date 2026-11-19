"""Build the local Serika pack from the verified official resource export."""
import json
import pathlib
import copy
import sys
from glb import load, save, read_accessor, append_accessor, append_view
import UnityPy

ROOT = pathlib.Path(__file__).resolve().parents[1]
newyear = '--newyear' in sys.argv
prefix = 'Serika_Newyear' if newyear else 'Serika_Original'
pack_id = 'serika_newyear' if newyear else 'serika'
export_root = ROOT / '.assets/exported' / pack_id
shared = ROOT / '.assets/common-textures/Character_Mouth.png'
if not shared.exists():
    env = UnityPy.load(*map(str, (ROOT / '.assets/selected').glob('*characters-_mxcommon*')))
    texture = next(o.read() for o in env.objects if o.type.name == 'Texture2D' and o.path_id == 6943113984227578831)
    shared.parent.mkdir(parents=True, exist_ok=True)
    texture.image.save(shared)
source = next(export_root.rglob(prefix + '.glb'))
target = ROOT / 'characters' / pack_id
target.mkdir(parents=True, exist_ok=True)
doc, binary = load(source)
choices = [
    ('idle', '待机', 'Cafe_Idle'),
    ('interact', '咖啡厅互动', 'Cafe_Reaction'),
    ('walk', '原地走路', 'Cafe_Walk'),
    ('victory', '胜利动作', 'Victory_Start'),
    ('reload', '换弹', 'Normal_Reload'),
    ('pickup', '编队提起', 'Formation_Pickup'),
]
if newyear:
    choices = [choice for choice in choices if choice[0] not in ('victory', 'reload')]
clips = doc['scenes'][0]['extras']['BAAD_unity_animation']['clips']
actions = []
mouth_events = {}
for action_id, label, suffix in choices:
    clip = next(c for c in clips if c['name'] == prefix + '_' + suffix)
    actions.append({'id': action_id, 'label': label, 'clip': clip['track']})
    mouth_events[clip['track']] = [{'time': e['time'], 'tile': e['int']} for e in clip['events'] if e['function'] == 'SetMouthTile']
doc['animations'] = [a for a in doc['animations'] if a['name'] in mouth_events]
doc['scenes'][0]['extras']['BAAD_unity_animation']['clips'] = [c for c in clips if c['track'] in mouth_events]
doc['extensionsUsed'] = ['KHR_materials_unlit']
for material in doc['materials']:
    material['extensions'] = {'KHR_materials_unlit': {}}
    material['pbrMetallicRoughness'].update({'metallicFactor': 0, 'roughnessFactor': 1})
    material['doubleSided'] = True
    if 'Eyebrow' in material['name']:
        material['pbrMetallicRoughness']['baseColorFactor'] = [0.041805096, 0.03871484, 0.09433961, 1] if newyear else [0.02645906, 0.0239854, 0.06603771, 1]

def embed_texture(file):
    view = append_view(doc, binary, file.read_bytes())
    image = len(doc['images'])
    doc['images'].append({'bufferView': view, 'mimeType': 'image/png'})
    texture = len(doc['textures'])
    doc['textures'].append({'source': image})
    return texture

if newyear:
    # These are actual cross-costume references in the official materials and
    # SkinnedMeshRenderer; the exporter does not resolve them automatically.
    for material in doc['materials']:
        source_name = {'Serika_Newyear_Face': 'Serika_Original_Face', 'Serika_Newyear_EyeMouth': 'Serika_Original_EyeMouth', 'DefaultMaterial': 'Serika_Original_Weapon'}.get(material['name'])
        if source_name:
            texture = embed_texture(next((ROOT / '.assets/exported/serika').rglob(source_name + '.png')))
            material['pbrMetallicRoughness']['baseColorTexture'] = {'index': texture}
            if material['name'] == 'DefaultMaterial': material['name'] = source_name

# Unity's eye/mouth shader uses separate texture inputs on disjoint triangles.
# Preserve the original geometry, skin weights and animated bones, but split
# those triangles into standard glTF primitives. Use the prefab behaviour's
# MouthDefaultUV (.25, .5), not the shared material's editor preview offset.
# Runtime SetMouthTile events shift this UV to the original animated tiles.
eye = next(p for p in doc['meshes'][0]['primitives'] if doc['materials'][p['material']]['name'].endswith('_EyeMouth'))
colors = read_accessor(doc, binary, eye['attributes']['COLOR_0'])
indices = [v[0] for v in read_accessor(doc, binary, eye['indices'])]
mouth_indices, eye_indices = [], []
for i in range(0, len(indices), 3):
    triangle = indices[i:i+3]
    mouth = all(0 < colors[v][3] < 255 for v in triangle)
    (mouth_indices if mouth else eye_indices).extend((v,) for v in triangle)
if not mouth_indices or not eye_indices:
    raise RuntimeError('Unexpected eye/mouth mesh layout')
mouth = copy.deepcopy(eye)
eye['indices'] = append_accessor(doc, binary, eye_indices, 'SCALAR', 5123)
mouth['indices'] = append_accessor(doc, binary, mouth_indices, 'SCALAR', 5123)
uv = read_accessor(doc, binary, eye['attributes']['TEXCOORD_0'])
default_uv = (0, .375) if newyear else (.25, .5)
mouth['attributes']['TEXCOORD_0'] = append_accessor(doc, binary, [(u * .5 + default_uv[0], v * .5 + .5 - default_uv[1]) for u, v in uv], 'VEC2')
mouth['material'] = len(doc['materials'])
mouth_texture = embed_texture(ROOT / '.assets/common-textures/Character_Mouth.png')
doc['materials'].append({'name': 'Serika_Original_Mouth', 'pbrMetallicRoughness': {'baseColorTexture': {'index': mouth_texture}, 'metallicFactor': 0, 'roughnessFactor': 1}, 'extensions': {'KHR_materials_unlit': {}}, 'alphaMode': 'MASK', 'alphaCutoff': .1, 'doubleSided': True})
doc['meshes'][0]['primitives'].append(mouth)
for mesh in doc['meshes']:
    for primitive in mesh['primitives']:
        # Vertex colors in these game meshes are shader masks, not albedo.
        primitive['attributes'].pop('COLOR_0', None)

# The source prefab already carries the halo transform. Restore the static
# mesh omitted by the upstream playable-model exporter using the original mesh.
halo_source = next(export_root.rglob('Serika_Newyear_Halo.glb' if newyear else 'Serika_Halo.glb'))
halo, halo_binary = load(halo_source)
view_base, accessor_base = len(doc['bufferViews']), len(doc['accessors'])
binary += b'\0' * (-len(binary) % 4)
base_offset = len(binary)
binary.extend(halo_binary)
for view in halo['bufferViews']:
    doc['bufferViews'].append({**view, 'byteOffset': view.get('byteOffset', 0) + base_offset})
for accessor in halo['accessors']:
    doc['accessors'].append({**accessor, 'bufferView': accessor['bufferView'] + view_base})
halo_material = len(doc['materials'])
halo_texture = embed_texture(next((ROOT / '.assets/exported/serika').rglob('Serika_Original_Halo.png')))
doc['materials'].append({'name': 'Serika_Halo', 'pbrMetallicRoughness': {'baseColorFactor': [.99607849, .22352943, .3019608, 1], 'baseColorTexture': {'index': halo_texture}, 'metallicFactor': 0, 'roughnessFactor': 1}, 'doubleSided': True, 'extensions': {'KHR_materials_unlit': {}}})
halo_mesh = copy.deepcopy(halo['meshes'][0])
for primitive in halo_mesh['primitives']:
    primitive['attributes'] = {k: v + accessor_base for k, v in primitive['attributes'].items()}
    primitive['indices'] += accessor_base
    primitive['material'] = halo_material
halo_node = next(n for n in doc['nodes'] if n['name'] == prefix + '_Halo')
halo_node['mesh'] = len(doc['meshes'])
doc['meshes'].append(halo_mesh)
save(target / 'model.glb', doc, binary)
manifest = {
    'id': pack_id, 'name': '芹香 · 新年' if newyear else '芹香 · 原版', 'model': 'model.glb',
    'source': {
        'url': 'https://prod-clientpatch.bluearchiveyostar.com/r96_nvji95owgkbcxlmkb8mi/Windows_PatchPack/BundlePackingInfo.json',
        'description': 'Blue Archive JP official Windows resources, r96 patch 33; Serika_Original with original animation events and MouthDefaultUV. Extracted with ZM-Kimu/Blue-Archive-Asset-Downloader and AssetRipper. Original game assets belong to their respective rights holders.'
    },
    'scale': 1, 'yaw': 0,
    'animations': {a['id']: a['clip'] for a in actions if a['id'] in ('idle', 'interact')},
    'actions': actions,
    'mouth': {'material': 'Serika_Original_Mouth', 'defaultTile': 300 if newyear else 402, 'events': mouth_events}
}
if newyear:
    manifest['source']['description'] = 'Official JP Windows r96 patch 33, Serika_Newyear; original new-year meshes, textures, rig and animation events. Official materials reference Serika_Original face, eyes, weapon and halo textures. MouthDefaultUV=(0,.375).'
(target / 'character.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
print(target)
