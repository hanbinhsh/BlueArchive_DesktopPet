"""Adapt verified official student prefabs using their own Unity materials."""
import copy
import re
import io
import json
import pathlib
import sys
import os
import struct
import UnityPy
from UnityPy.helpers.MeshHelper import MeshHandler
from glb import load, save, read_accessor, append_accessor, append_view
from visibility import attach_visibility
from mouth_events import mouth_events, normalize_repeat_uv
from rigid_geometry import rebuild_rigid_mesh
from renderer_event_layout import renderer_event_layout
from prop_materials import adapt_prop_material
from prop_visibility import apply_prop_visibility

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = ROOT / '.assets'
SPECS = {
    'junko': ('Zunko_Original', '纯子 · 原版'),
    'junko_newyear': ('CH0192', '纯子 · 新年'),
    'serika_swimsuit': ('CH0189', '芹香 · 泳装'),
}
SPECS.update(json.loads((ROOT/'scripts/roster-expansion.json').read_text(encoding='utf-8')))
SPECS.update(json.loads((ROOT/'scripts/roster-wave3.json').read_text(encoding='utf-8')))
SPECS.update(json.loads((ROOT/'scripts/roster-wave4.json').read_text(encoding='utf-8')))
SPECS.update(json.loads((ROOT/'scripts/roster-wave5.json').read_text(encoding='utf-8')))
SPECS.update(json.loads((ROOT/'scripts/roster-wave6.json').read_text(encoding='utf-8')))
SPECS.update(json.loads((ROOT/'scripts/roster-wave7.json').read_text(encoding='utf-8')))
pack = sys.argv[1]
if os.environ.get('BA_ROSTER_SPECS'): SPECS.update(json.loads(pathlib.Path(os.environ['BA_ROSTER_SPECS']).read_text(encoding='utf8')))
prefix, label = SPECS[pack]
profiles = json.loads(pathlib.Path(os.environ['BA_ROSTER_PROFILES']).read_text(encoding='utf8')) if os.environ.get('BA_ROSTER_PROFILES') else {}
profile = profiles.get(pack, {})
model_prefix = profile.get('modelPrefix', {'toki':'CH0187_CafeOnly', 'hoshino_battle':'CH0258_01'}.get(pack, prefix))
prefab_name = profile.get('prefabName', model_prefix)
export = WORK / 'exported' / profile.get('exportDirectory', pack)
candidates = [p for p in export.rglob(model_prefix + '*.glb') if p.stat().st_size>=20 and re.fullmatch(re.escape(model_prefix)+r'(?:_\d+)?', p.stem)]
def prefab_score(path):
    # A static mesh export can have the same filename as its animated prefab.
    # Prefer the original animation metadata instead of relying on export order.
    with path.open('rb') as stream:
        header=stream.read(20);data=json.loads(stream.read(struct.unpack_from('<I',header,12)[0]))
    metadata=any(s.get('extras',{}).get('BAAD_unity_animation') for s in data.get('scenes',[]))
    return (bool(metadata),len(data.get('animations',[])),path.stat().st_mtime)
doc, binary = load(max(candidates, key=prefab_score))
source_dirs = [pathlib.Path(p) for p in json.loads(os.environ.get('BA_SOURCE_DIRS', '[]'))] or [WORK/'selected']
source_files = {p.name:p for folder in source_dirs for p in folder.glob('*.bundle')}
env = globals().get('source_environment') or UnityPy.load(*map(str, source_files.values()))
materials, renderers, halo_meshes, defaults = {}, {}, {}, []
halo_original_meshes = {}
renderer_names, initial_visibility = [], {}
original_skins = {}
original_renderers = {}
def walk_renderers(go, parent_active=True):
    active = parent_active and bool(go.m_IsActive)
    for component in go.m_Component:
        if component.component.deref().type.name not in ('Transform', 'SkinnedMeshRenderer', 'MeshRenderer'): continue
        value = component.component.read()
        if value.object_reader.type.name in ('SkinnedMeshRenderer', 'MeshRenderer'):
            renderer_names.append(go.m_Name)
            initial_visibility[go.m_Name] = bool(value.m_Enabled and active)
            original_renderers[go.m_Name] = value
            if value.object_reader.type.name == 'SkinnedMeshRenderer': original_skins[go.m_Name] = value
        if value.object_reader.type.name == 'Transform':
            for child in value.m_Children: walk_renderers(child.read().m_GameObject.read(), active)
for obj in env.objects:
    if obj.type.name == 'Material':
        mat = obj.read(); materials[mat.m_Name] = mat
    elif obj.type.name in ('SkinnedMeshRenderer', 'MeshRenderer'):
        renderer = obj.read()
        try:
            name = renderer.m_GameObject.read().m_Name
            renderers[name] = [p.read().m_Name for p in renderer.m_Materials]
        except Exception: pass
    elif obj.type.name == 'MeshFilter':
        mesh_filter = obj.read()
        try:
            name = mesh_filter.m_GameObject.read().m_Name
            if 'Halo' in name:
                original_mesh = mesh_filter.m_Mesh.read()
                halo_meshes[name] = original_mesh.m_Name
                halo_original_meshes[name] = original_mesh
        except Exception: pass
    elif obj.type.name == 'MonoBehaviour':
        data = obj.read_typetree()
        if 'MouthDefaultUV' in data:
            try:
                go = obj.read().m_GameObject.read().m_Name
                has_mouth=bool(data.get('MouthRenderer', {}).get('m_PathID'))
                authored_no_mouth=profile.get('noMouthAtlas',False) and not has_mouth and data.get('MouthMaterialIndex')==-1
                if go == prefab_name and (has_mouth or authored_no_mouth):
                    defaults.append(data['MouthDefaultUV'])
                    renderer_names.clear(); initial_visibility.clear()
                    walk_renderers(obj.read().m_GameObject.read())
            except Exception as error: print('Prefab metadata:', error)
if not defaults: raise RuntimeError('Missing original MouthDefaultUV')
# Skill-cut prefabs can reuse renderer names with a different material layout.
for name, renderer in original_renderers.items():
    if 'Halo' in name:
        for component in renderer.m_GameObject.read().m_Component:
            if component.component.deref().type.name == 'MeshFilter':
                original_mesh = component.component.read().m_Mesh.read()
                halo_meshes[name] = original_mesh.m_Name
                halo_original_meshes[name] = original_mesh
    if renderer.m_Materials and all(not p.m_PathID for p in renderer.m_Materials):
        # Unity renders nothing when every material slot is null. NonWeapon
        # scene prefabs deliberately use this for the weapon and star meshes.
        # Keep transforms for animation, but never synthesize a visible material.
        initial_visibility[name] = False
        for node in doc['nodes']:
            if node.get('name') == name:
                node.pop('mesh', None); node.pop('skin', None)
        continue
    try:
        resolved_mats = [p.read() for p in renderer.m_Materials]
    except FileNotFoundError:
        initial_visibility[name] = False
        for node in doc['nodes']:
            if node.get('name') == name:
                node.pop('mesh', None); node.pop('skin', None)
        continue
    renderers[name] = [m.m_Name for m in resolved_mats]
    # Glow and outline materials can have identical names. Prefer the material
    # actually referenced by this prefab, not another asset's same-named copy.
    for material in resolved_mats:
        materials[material.m_Name] = material
default_uv = profile.get('mouthDefaultUV', defaults[0])
default_tile = round(default_uv['y'] * 8) * 100 + round(default_uv['x'] * 8)
texture_cache = {}
def texture_index(texture):
    key = (texture.object_reader.assets_file.name, texture.object_reader.path_id)
    if key in texture_cache: return texture_cache[key]
    out = io.BytesIO(); texture.image.save(out, format='PNG')
    image = len(doc.setdefault('images', []))
    doc['images'].append({'bufferView': append_view(doc, binary, out.getvalue()), 'mimeType': 'image/png'})
    index = len(doc.setdefault('textures', [])); doc['textures'].append({'source': image})
    texture_cache[key] = index
    return index

material_cache = {}
def material_index(name):
    if name in material_cache: return material_cache[name]
    original = materials[name]
    properties = original.m_SavedProperties
    textures = dict(properties.m_TexEnvs); colors = dict(properties.m_Colors)
    pbr = {'metallicFactor': 0, 'roughnessFactor': 1}
    if '_MainTex' in textures and textures['_MainTex'].m_Texture.m_PathID:
        pbr['baseColorTexture'] = {'index': texture_index(textures['_MainTex'].m_Texture.read())}
    color = colors.get('_Color') if 'Halo' in name else colors.get('_Tint') if 'Eyebrow' in name else None
    if color: pbr['baseColorFactor'] = [color.r, color.g, color.b, color.a]
    result = {'name': name, 'pbrMetallicRoughness': pbr, 'extensions': {'KHR_materials_unlit': {}}, 'doubleSided': True}
    floats = dict(properties.m_Floats)
    # Unity SrcAlpha / OneMinusSrcAlpha hair layers carry genuine alpha.
    # Do not infer transparency from an RGBA image alone (body masks also use it).
    if floats.get('_SrcBlend') == 5 and floats.get('_DstBlend') == 10:
        result['alphaMode'] = 'BLEND'
        result['doubleSided'] = floats.get('_Cull', 0) == 0
    try:
        if original.m_Shader.m_PathID:
            shader_name = original.m_Shader.read().m_ParsedForm.m_Name
            if shader_name == 'MX/C-Simple-Transparent' and '_Tint' in colors:
                tint = [max(0, min(1, getattr(colors['_Tint'], k))) for k in 'rgba']
                result['pbrMetallicRoughness']['baseColorFactor'] = tint
                result['alphaMode'] = 'BLEND'
                result.setdefault('extras', {}).update(BA_sourceShader=shader_name, BA_sourceColorProperty='_Tint', BA_depthWrite=False)
            elif shader_name == 'MX/C-General/Transparent':
                result['alphaMode'] = 'BLEND'
                result['doubleSided'] = floats.get('_Cull', 0) == 0
    except Exception:
        pass
    adapt_prop_material(result)
    index = len(doc['materials']); doc['materials'].append(result); material_cache[name] = index
    return index

doc['extensionsUsed'] = ['KHR_materials_unlit']
# Unity permits rigid skinning with a single bone index and no weight stream.
# Recover that original binding instead of the exporter's synthesized weights.
rigid_repairs = []
for node in doc['nodes']:
    if 'mesh' not in node or 'skin' not in node: continue
    original = original_skins.get(node.get('name'))
    if original is None: continue
    source = MeshHandler(original.m_Mesh.read()); source.process()
    indices = source.m_BoneIndices
    # Some Unity submeshes overlap vertex ranges (e.g. CH0280 bangs).
    # Export can silently omit faces even though surviving weights and bind
    # matrices are correct. Recover the authored topology before adapting it.
    primitives=doc['meshes'][node['mesh']]['primitives']
    source_triangles=source.get_triangles()
    if source.m_BoneWeights is not None and len(primitives)==len(source_triangles) and any(
        doc['accessors'][p['indices']]['count']!=len(t)*3 for p,t in zip(primitives,source_triangles)
    ):
        joints=doc['skins'][node['skin']]['joints']
        joint_names=[doc['nodes'][j]['name'] for j in joints]
        remap=[joint_names.index(b.read().m_GameObject.read().m_Name) for b in original.m_Bones]
        rebuild_rigid_mesh(doc,binary,node,original,source,remap,weighted=True)
    if source.m_BoneWeights is not None or not indices or not all(len(v) == 1 for v in indices): continue
    joints = doc['skins'][node['skin']]['joints']
    joint_names = [doc['nodes'][j]['name'] for j in joints]
    remap = [joint_names.index(b.read().m_GameObject.read().m_Name) for b in original.m_Bones]
    by_position, vertices_at_position = {}, {}
    for vertex, (position, index) in enumerate(zip(source.m_Vertices, indices)):
        key = tuple(round(v, 6) for v in (-position[0], position[1], position[2]))
        by_position.setdefault(key, set()).add(remap[index[0]])
        vertices_at_position.setdefault(key, []).append(vertex)
        # Separate rigid props can share a position while belonging to different
        # joints. UVs and normals preserve their original surface identity.
    rebuilt_rigid = False
    for primitive in doc['meshes'][node['mesh']]['primitives']:
        bindings = []
        uv_values = read_accessor(doc, binary, primitive['attributes']['TEXCOORD_0'])
        normal_values = read_accessor(doc, binary, primitive['attributes']['NORMAL'])
        for vertex, position in enumerate(read_accessor(doc, binary, primitive['attributes']['POSITION'])):
            key = tuple(round(v, 6) for v in position)
            matches = by_position.get(key, set())
            if len(matches) > 1:
                uv, normal = uv_values[vertex], normal_values[vertex]
                candidates = []
                for v in vertices_at_position[key]:
                    su, sn = source.m_UV0[v], source.m_Normals[v]
                    if max(abs(a-b) for a,b in zip((*uv,*normal),(su[0],1-su[1],-sn[0],sn[1],sn[2]))) < 1e-4:
                        candidates.append(remap[indices[v][0]])
                matches = set(candidates)
            if len(matches) != 1:
                rebuild_rigid_mesh(doc,binary,node,original,source,remap)
                rebuilt_rigid=True
                break
            bindings.append((next(iter(matches)), 0, 0, 0))
        if rebuilt_rigid:break
        primitive['attributes']['JOINTS_0'] = append_accessor(doc, binary, bindings, 'VEC4', 5123)
        primitive['attributes']['WEIGHTS_0'] = append_accessor(doc, binary, [(1,0,0,0)] * len(bindings), 'VEC4')
    rigid_repairs.append(node['name'])
doc.setdefault('extras', {})['BA_rigid_skin_repairs'] = rigid_repairs
for node in doc['nodes']:
    if 'mesh' not in node: continue
    mesh = doc['meshes'][node['mesh']]
    names = renderers.get(node['name'])
    for i, primitive in enumerate(mesh['primitives']):
        name = doc['materials'][primitive['material']]['name']
        if name == 'DefaultMaterial':
            if not names or len(names) != len(mesh['primitives']): raise RuntimeError('Unresolved merged material: '+node['name'])
            name = names[i]
        primitive['material'] = material_index(name)

mouth_material = None
mouth_index = None
mouth_columns = mouth_rows = 8
for mesh in doc['meshes']:
    for eye in list(mesh['primitives']):
        mat = doc['materials'][eye['material']]
        original = materials.get(mat['name'])
        if original is None: continue
        mouth_slot = dict(original.m_SavedProperties.m_TexEnvs).get('_MouthTileTex')
        # CH0163's authored material is spelled EyeMoutn. Shader properties,
        # rather than material naming, determine whether it has a mouth atlas.
        if mouth_slot is None or not mouth_slot.m_Texture.m_PathID: continue
        floats = dict(original.m_SavedProperties.m_Floats)
        mouth_columns = round(floats.get('_MouthTileCols', 8))
        mouth_rows = round(floats.get('_MouthTileRows', 8))
        envs = dict(original.m_SavedProperties.m_TexEnvs)
        mouth_tex = envs['_MouthTileTex']
        texture = mouth_tex.m_Texture.read()
        settings = texture.m_TextureSettings
        wraps = [getattr(settings, axis, getattr(settings, 'm_WrapMode', None)) for axis in ('m_WrapU', 'm_WrapV')]
        normalized_uv = normalize_repeat_uv(default_uv, *wraps)
        if normalized_uv != default_uv:
            doc.setdefault('extras', {})['BA_mouth_uv_normalization'] = {'original': dict(default_uv), 'normalized': normalized_uv, 'texture': texture.m_Name, 'wrapU': wraps[0], 'wrapV': wraps[1]}
            default_uv = normalized_uv
        default_tile = round(default_uv['y'] * mouth_rows) * 100 + round(default_uv['x'] * mouth_columns)
        uv = read_accessor(doc, binary, eye['attributes']['TEXCOORD_0'])
        indices = [v[0] for v in read_accessor(doc, binary, eye['indices'])]
        mouth_ids, eye_ids = [], []
        # The mouth is a connected UV island. Some originals (notably New Year
        # Mutsuki) mix zero/nonzero vertex alpha inside that island; alpha-only
        # selection leaves triangles sampling the eye atlas over the upper lip.
        adjacency = {}
        for i in range(0, len(indices), 3):
            triangle = indices[i:i+3]
            for vertex in triangle: adjacency.setdefault(vertex, set()).update(triangle)
        unseen = set(indices); mouth_vertices = set()
        while unseen:
            group = set(); todo = [next(iter(unseen))]
            while todo:
                vertex = todo.pop()
                if vertex in group: continue
                group.add(vertex); todo.extend(adjacency[vertex] - group)
            unseen -= group
            if all(uv[v][0] <= .2501 and uv[v][1] >= .7499 for v in group): mouth_vertices.update(group)
        for i in range(0, len(indices), 3):
            triangle = indices[i:i+3]
            (mouth_ids if all(v in mouth_vertices for v in triangle) else eye_ids).extend((v,) for v in triangle)
        if not mouth_ids: continue
        mouth = copy.deepcopy(eye)
        if eye_ids: eye['indices'] = append_accessor(doc, binary, eye_ids, 'SCALAR', 5123)
        else: mesh['primitives'].remove(eye)
        mouth['indices'] = append_accessor(doc, binary, mouth_ids, 'SCALAR', 5123)
        sx, sy = abs(mouth_tex.m_Scale.x), abs(mouth_tex.m_Scale.y)
        mouth['attributes']['TEXCOORD_0'] = append_accessor(doc, binary, [(u*sx + default_uv['x'], v*sy + 1-sy-default_uv['y']) for u,v in uv], 'VEC2')
        mouth_material = prefix + '_Mouth'
        if mouth_index is None:
            mouth_index = len(doc['materials'])
            doc['materials'].append({'name': mouth_material, 'pbrMetallicRoughness': {'baseColorTexture': {'index': texture_index(mouth_tex.m_Texture.read())}}, 'extensions': {'KHR_materials_unlit': {}}, 'doubleSided': True, 'alphaMode': 'MASK', 'alphaCutoff': .1})
        mouth['material'] = mouth_index
        mesh['primitives'].append(mouth)
for mesh in doc['meshes']:
    for primitive in mesh['primitives']: primitive['attributes'].pop('COLOR_0', None)

for halo_name, mesh_name in halo_meshes.items():
    matches = [n for n in doc['nodes'] if re.fullmatch(re.escape(halo_name)+r'(?:_\d+)?',n.get('name',''))]
    if not matches: continue
    node = matches[-1]
    if 'mesh' in node: continue
    # Same-named halo meshes can use different units/pivots across costumes.
    # Rebuild the mesh actually referenced by this prefab, never a global name match.
    source = MeshHandler(halo_original_meshes[halo_name]); source.process()
    positions = [(-v[0],v[1],v[2]) for v in source.m_Vertices]
    attributes = {'POSITION':append_accessor(doc,binary,positions,'VEC3')}
    doc['accessors'][attributes['POSITION']].update(min=[min(v[i] for v in positions) for i in range(3)],max=[max(v[i] for v in positions) for i in range(3)])
    if source.m_Normals: attributes['NORMAL']=append_accessor(doc,binary,[(-v[0],v[1],v[2]) for v in source.m_Normals],'VEC3')
    if source.m_UV0: attributes['TEXCOORD_0']=append_accessor(doc,binary,[(v[0],1-v[1]) for v in source.m_UV0],'VEC2')
    mesh={'name':mesh_name,'primitives':[]}
    for i,triangles in enumerate(source.get_triangles()):
        if not triangles:continue
        mesh['primitives'].append({'attributes':attributes,'indices':append_accessor(doc,binary,[(v,) for a,b,c in triangles for v in (a,c,b)],'SCALAR',5125),'material':material_index(renderers[halo_name][i])})
    node['mesh']=len(doc['meshes']);doc['meshes'].append(mesh)

clips = doc['scenes'][0]['extras']['BAAD_unity_animation']['clips']
choices = [('idle','待机','Cafe_Idle'),('interact','咖啡厅互动','Cafe_Reaction'),('walk','原地走路','Cafe_Walk'),('victory','胜利动作','Victory_Start'),('reload','换弹','Normal_Reload'),('pickup','编队提起','Formation_Pickup')]
if profile: choices = profile['actions']
actions, events = [], {}
for id, name, suffix in choices:
    animation_prefix = 'CH0258_01' if pack == 'hoshino_battle' else prefix
    clip_name = suffix if profile else animation_prefix+'_'+suffix
    clip = next((c for c in clips if c['name'] == clip_name), None)
    if not clip:
        if profile: raise ValueError('Missing declared original clip: '+clip_name)
        continue
    # A metadata entry can survive even when native path hashes failed to bind.
    # Never publish a role that has no actual transform/morph animation.
    playable = next((a for a in doc.get('animations', []) if a['name'] == clip['track']), None)
    if playable is None or not playable.get('channels'):
        raise ValueError('Declared original clip has no exported channels: '+clip_name)
    actions.append({'id':id,'label':name,'clip':clip['track']})
    events[clip['track']] = mouth_events(clip, default_tile)
assert ({'idle','interact'} if profile else {'idle','interact','pickup'}) <= {a['id'] for a in actions}
doc['animations'] = [a for a in doc['animations'] if a['name'] in events]
doc['scenes'][0]['extras']['BAAD_unity_animation']['clips'] = [c for c in clips if c['track'] in events]
if placement := profile.get('recenterTranslations'):
    # Scene interactions can contain a constant world-placement offset in the
    # pelvis channel. Translate its value keys into the own idle's frame; keep
    # authored motion deltas and cubic tangents intact.
    node_index = next(i for i,n in enumerate(doc['nodes']) if n['name']==placement['node'])
    def translation_sampler(animation):
        channel = next(c for c in animation['channels'] if c['target']=={'node':node_index,'path':'translation'})
        return animation['samplers'][channel['sampler']]
    idle_clip = next(a for a in doc['animations'] if a['name']==next(a['clip'] for a in actions if a['id']=='idle'))
    idle_sampler = translation_sampler(idle_clip)
    idle_values = read_accessor(doc,binary,idle_sampler['output'])
    anchor = idle_values[1 if idle_sampler.get('interpolation')=='CUBICSPLINE' else 0]
    offsets=[]
    for name in placement['clips']:
        meta=next(c for c in clips if c['name']==name)
        animation=next(a for a in doc['animations'] if a['name']==meta['track'])
        sampler=translation_sampler(animation);values=read_accessor(doc,binary,sampler['output'])
        cubic=sampler.get('interpolation')=='CUBICSPLINE';first=values[1 if cubic else 0]
        delta=[anchor[i]-first[i] for i in range(3)]
        corrected=[tuple(v[i]+delta[i] for i in range(3)) if not cubic or j%3==1 else v for j,v in enumerate(values)]
        sampler['output']=append_accessor(doc,binary,corrected,'VEC3')
        offsets.append({'clip':meta['track'],'node':node_index,'translation':delta})
    doc['scenes'][0]['extras']['BA_scene_placement_offsets']=offsets
target = pathlib.Path(os.environ.get('BA_CHARACTER_OUTPUT', ROOT/'characters')) / pack; target.mkdir(exist_ok=True, parents=True)
# CH0192's authored events retain indices from the earlier renderer layout;
# the r96 prefab has fewer renderers. Reconcile its two named face variants.
if pack == 'junko_newyear':
    renderer_names = [''] * 11
    renderer_names[9] = 'CH0192_Body_Face01_Outline'
    renderer_names[10] = 'CH0192_Body_Face_Outline'
face_event_layouts = {
    'aoba': {2:'CH0288_Face_Outline', 3:'CH0288_Face01_Outline', 4:'CH0288_Face02_Outline'},
    'reisa': {5:'CH0167_Body_Face01_Outline', 6:'CH0167_Body_Face_Outline'},
    'koyuki': {3:'CH0198_Face01_Outline', 4:'CH0198_Face_Outline'},
    'koyuki_pajamas': {4:'CH0310_Face01_Mesh', 5:'CH0310_Face02_Mesh'},
}
for index, name in face_event_layouts.get(pack, {}).items(): renderer_names[index] = name
renderer_names=renderer_event_layout(pack,renderer_names)
for index,name in profile.get('rendererEventLayout',{}).items():
    while len(renderer_names)<=int(index): renderer_names.append('')
    renderer_names[int(index)]=name
if profile.get('rendererEventLayout'):
    doc.setdefault('extras',{})['BA_renderer_event_layout']=profile['rendererEventLayout']
for node in doc['nodes']:
    base = re.sub(r'_\d+$', '', node.get('name',''))
    if 'mesh' in node and base in initial_visibility and node['name'] not in initial_visibility:
        initial_visibility[node['name']] = initial_visibility[base]
attach_visibility(doc, renderer_names, initial_visibility, ignore_missing=pack == 'toki' or profile.get('ignoreMissingVisibility',False), ignored_events=profile.get('ignoredRendererEvents',[]))
apply_prop_visibility(doc, pack)
save(target/'model.glb',doc,binary)
manifest = {'id':pack,'name':label,'model':'model.glb','source':{'url':'https://prod-clientpatch.bluearchiveyostar.com/r96_nvji95owgkbcxlmkb8mi/Windows_PatchPack/BundlePackingInfo.json','description':f'Official JP r96 patch 33 {prefix}; original rig, textures, material references, mouth defaults and animation events.'},'scale':1,'yaw':0,'animations':{a['id']:a['clip'] for a in actions if a['id'] in ['idle','interact']},'actions':actions}
if profile.get('note'): manifest['note'] = profile['note']
manifest['scale']=profile.get('scale',1)
if profile.get('framing'):manifest['framing']=profile['framing']
if mouth_material: manifest['mouth']={'material':mouth_material,'defaultTile':default_tile,'columns':mouth_columns,'rows':mouth_rows,'baseUV':[default_uv['x'],default_uv['y']],'events':events}
(target/'character.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
print(pack,len(doc['animations']),default_uv, [name for name in halo_meshes if any(n.get('name') == name for n in doc['nodes'])])
