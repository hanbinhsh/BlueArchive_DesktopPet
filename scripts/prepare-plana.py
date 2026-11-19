"""Convert original Plana timeline clips and separate facial renderers."""
import pathlib, json, io, copy
import UnityPy
import numpy as np
from glb import load, save, append_view
from visibility import attach_visibility
ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = ROOT / '.assets'
export = WORK / 'exported' / 'plana-animated'
doc, binary = load(next(export.rglob('Plana_Original_Mesh.glb')))
env = UnityPy.load(*map(str,(WORK/'selected').glob('*.bundle')))
materials, renderers = {}, {}
for obj in env.objects:
    if obj.type.name == 'Material':
        m=obj.read(); materials[m.m_Name]=m
    elif obj.type.name == 'SkinnedMeshRenderer':
        r=obj.read()
        try: renderers[r.m_GameObject.read().m_Name]=[p.read().m_Name for p in r.m_Materials]
        except Exception: pass
texture_cache = {}
def texture_index(texture):
    key = texture.object_reader.path_id
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
    index = len(doc['materials']); doc['materials'].append(result); material_cache[name] = index
    return index

doc['extensionsUsed'] = ['KHR_materials_unlit']
for node in doc['nodes']:
    if 'mesh' not in node: continue
    mesh = doc['meshes'][node['mesh']]
    names = renderers.get(node['name'])
    for i, primitive in enumerate(mesh['primitives']):
        name = names[i] if names and i < len(names) else doc['materials'][primitive['material']]['name']
        primitive['material'] = material_index(name)


for mesh in doc['meshes']:
    for primitive in mesh['primitives']: primitive['attributes'].pop('COLOR_0', None)
# The halo is an independent official prefab, positioned by its own Transform.
halo,data=load(next(export.rglob('Plana_Original_Halo.glb')))
binary += b'\0' * (-len(binary)%4)
start,vbase,abase=len(binary),len(doc['bufferViews']),len(doc['accessors'])
binary.extend(data)
doc['bufferViews'].extend({**v,'byteOffset':v.get('byteOffset',0)+start} for v in halo['bufferViews'])
doc['accessors'].extend({**a,'bufferView':a['bufferView']+vbase} for a in halo['accessors'])
mesh=copy.deepcopy(halo['meshes'][0])
for p in mesh['primitives']:
    p['attributes']={k:v+abase for k,v in p['attributes'].items() if k!='COLOR_0'}
    p['indices']+=abase;p['material']=material_index('Plana_Original_Halo')
transform=None
for obj in env.objects:
    if obj.type.name=='Transform':
        t=obj.read()
        if t.m_GameObject.read().m_Name=='Plana_Original_Halo': transform=t;break
assert transform
p,q=transform.m_LocalPosition,transform.m_LocalRotation
# AssetRipper GLB changes Unity handedness by negating X.
node={'name':'Plana_Original_Halo','mesh':len(doc['meshes']),'translation':[-p.x,p.y,p.z],'rotation':[q.x,-q.y,-q.z,q.w]}
def matrix(n):
    if 'matrix' in n: return np.array(n['matrix']).reshape(4,4).T
    x,y,z,w=n.get('rotation',[0,0,0,1])
    m=np.eye(4)
    m[:3,:3]=np.array([[1-2*y*y-2*z*z,2*x*y-2*z*w,2*x*z+2*y*w],[2*x*y+2*z*w,1-2*x*x-2*z*z,2*y*z-2*x*w],[2*x*z-2*y*w,2*y*z+2*x*w,1-2*x*x-2*y*y]]) @ np.diag(n.get('scale',[1,1,1]))
    m[:3,3]=n.get('translation',[0,0,0]);return m
parents={c:i for i,n in enumerate(doc['nodes']) for c in n.get('children',[])}
def world(i): return (world(parents[i]) if i in parents else np.eye(4)) @ matrix(doc['nodes'][i])
head=next(i for i,n in enumerate(doc['nodes']) if n['name']=='Bip001 Head')
local=np.linalg.inv(world(head)) @ matrix(node)
# Raise the separate halo above the NPC hair; its prefab origin is lower.
local[0,3] += .26
node.pop('translation');node.pop('rotation');node['matrix']=local.T.flatten().tolist()
doc['nodes'][head].setdefault('children',[]).append(len(doc['nodes']))
doc['nodes'].append(node);doc['meshes'].append(mesh)
clips=doc['scenes'][0]['extras']['BAAD_unity_animation']['clips']
choices=[('idle','待机','Idle'),('interact','回应','Reaction'),('smile','微笑','Smile'),('blink','眨眼','Blink'),('blink2','眨眼（二）','Blink_02')]
actions=[]
for id,label,suffix in choices:
    clip=next(c for c in clips if c['name']=='Plana_Original_AroPla_Cacha_02_'+suffix)
    actions.append({'id':id,'label':label,'clip':clip['track']})
tracks={a['clip'] for a in actions}
doc['animations']=[a for a in doc['animations'] if a['name'] in tracks]
doc['scenes'][0]['extras']['BAAD_unity_animation']['clips']=[c for c in clips if c['track'] in tracks]
attach_visibility(doc,[])
target=ROOT/'characters'/'plana';target.mkdir(exist_ok=True)
save(target/'model.glb',doc,binary)
manifest={'id':'plana','name':'普拉娜 · 原版（NPC）','model':'model.glb','source':{'url':'https://prod-clientpatch.bluearchiveyostar.com/r96_nvji95owgkbcxlmkb8mi/Windows_PatchPack/BundlePackingInfo.json','description':'Official JP r96 patch 33 Plana NPC prefab and original AroPla_Cacha_02 timeline clips. Original facial renderer visibility curves; no Formation_Pickup exists.'},'scale':1,'yaw':0,'animations':{a['id']:a['clip'] for a in actions if a['id'] in ['idle','interact']},'actions':actions}
manifest['idleBlink']={'action':'blink','interval':6}
(target/'character.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Plana:',len(doc['animations']),'clips')
