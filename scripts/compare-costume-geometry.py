"""Content comparison: different CAB/path IDs do not imply different clothes."""
import hashlib, json, pathlib
import UnityPy
from UnityPy.helpers.MeshHelper import MeshHandler

R=pathlib.Path(__file__).resolve().parents[1]; W=R/'.assets'
files={p.name:p for folder in [W/'selected',W/'costume-audit',W/'costume-variants']
       for p in folder.glob('*.bundle')}
env=UnityPy.load(*map(str,files.values()))
objects={(o.assets_file.name.lower(),o.path_id):o for o in env.objects}
roots=json.loads((R/'test-results/costume-source-variants.json').read_text(encoding='utf8'))['roots']
roots={r['name']:r for r in roots}
cache={}
def digest(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def texture(p):
    if not p.m_PathID:return None
    t=p.read(); image=t.image.convert('RGBA')
    return {'size':image.size,'pixelsSha256':hashlib.sha256(image.tobytes()).hexdigest()}
def signature(ref):
    key=tuple(ref)
    if key in cache:return cache[key]
    if key[0] == 'unity default resources':
        return {'type':'UnityBuiltin','name':str(key[1]),'builtinId':key[1]}
    obj=objects[key]
    data=obj.read()
    if obj.type.name=='Mesh':
        mesh=MeshHandler(data);mesh.process()
        value={'vertices':mesh.m_Vertices,'uv':mesh.m_UV0,'triangles':mesh.get_triangles()}
        result={'type':'Mesh','name':data.m_Name,'vertices':len(mesh.m_Vertices),'geometrySha256':digest(value)}
    else:
        props=data.m_SavedProperties
        textures={k: {'texture':texture(v.m_Texture),'scale':[v.m_Scale.x,v.m_Scale.y],
                      'offset':[v.m_Offset.x,v.m_Offset.y]} for k,v in props.m_TexEnvs}
        value={'textures':textures,'floats':dict(props.m_Floats),
               'colors':{k:[v.r,v.g,v.b,v.a] for k,v in props.m_Colors},
               'shaderKeywords':getattr(data,'m_ShaderKeywords',None)}
        result={'type':'Material','name':data.m_Name,'propertiesSha256':digest(value),
                'textureHashes':{k:v['texture'] for k,v in textures.items()}}
    cache[key]=result
    return result
def renderer(r):
    return {'node':r['node'],'enabled':r['enabled'],'active':r['active'],
            'mesh':signature(r['mesh']), 'materials':[signature(m) for m in r['materials'] if m]}
pairs=[
    ('CH0187_CafeOnly','CH0187'),('CH0187','Toki_CNC_MG_Boss'),
    ('CH0263','CH0263_Scenario01'),('CH0333','CH0333_Scenario'),
    ('CH0334','CH0334_Carrier'),('CH0334','CH0334_Scenario'),
    ('CH0335','CH0335_Carrier'),('CH0335','CH0335_Carrier2'),
    ('CH0335','CH0335_Scenario_01'),('CH0335','CH0335_Scenario_02'),
    ('CH0335_Carrier','CH0335_Scenario_01')]
results=[]
for base,other in pairs:
    row={'baseline':base,'variant':other,
         'baselineRenderers':[renderer(r) for r in roots[base]['renderers']],
         'variantRenderers':[renderer(r) for r in roots[other]['renderers']]}
    results.append(row)
    print(base,'=>',other,flush=True)
(R/'test-results/costume-geometry-comparison.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
print('Compared',len(results),'pairs;',len(cache),'unique mesh/material source objects.')
