"""Compare each new halo against its own Unity prefab's MeshFilter reference."""
import json, pathlib, re
import UnityPy
from UnityPy.helpers.MeshHelper import MeshHandler
from glb import load, read_accessor
R=pathlib.Path(__file__).resolve().parents[1]
specs=json.loads((R/'scripts/roster-wave11.json').read_text(encoding='utf8'))
files={p.name:p for folder in ['selected','costume-audit','costume-variants'] for p in (R/'.assets'/folder).glob('*.bundle')}
env=UnityPy.load(*map(str,files.values()))
roots={}
for obj in env.objects:
    if obj.type.name!='MonoBehaviour':continue
    raw=obj.read_typetree()
    if 'MouthDefaultUV' not in raw or not raw.get('MouthRenderer',{}).get('m_PathID'):continue
    go=obj.read().m_GameObject.read()
    if go.m_Name in {v[0] for v in specs.values()}:roots[go.m_Name]=go

def halos(go):
    for component in go.m_Component:
        kind=component.component.deref().type.name
        if kind=='MeshFilter' and 'Halo' in go.m_Name:
            yield go.m_Name,component.component.read().m_Mesh.read()
        elif kind=='Transform':
            for child in component.component.read().m_Children:yield from halos(child.read().m_GameObject.read())

report=[]
for key,(prefix,_) in specs.items():
    doc,data=load(R/'.assets/expanded-ready'/key/'model.glb');checked=[]
    for name,mesh in halos(roots[prefix]):
        nodes=[n for n in doc['nodes'] if re.fullmatch(re.escape(name)+r'(?:_\d+)?',n.get('name',''))]
        assert nodes and 'mesh' in nodes[-1],(key,name)
        primitives=doc['meshes'][nodes[-1]['mesh']]['primitives'];source=MeshHandler(mesh);source.process()
        expected=[(-v[0],v[1],v[2]) for v in source.m_Vertices]
        for primitive in primitives:
            actual=read_accessor(doc,data,primitive['attributes']['POSITION'])
            assert len(actual)==len(expected),(key,name,len(actual),len(expected))
            assert all(abs(a-b)<1e-7 for av,bv in zip(actual,expected) for a,b in zip(av,bv)),(key,name,'geometry differs from referenced source')
        checked.append({'name':name,'vertices':len(expected),'sourceFile':mesh.object_reader.assets_file.name,'sourcePathId':mesh.object_reader.path_id})
    assert checked,key
    report.append({'character':key,'originalGeometry':checked})
    if key=='hasumi':
        proof=doc['extras']['BA_mouth_uv_normalization'];assert proof['wrapV']==0 and proof['original']['y']==2.5 and proof['normalized']['y']==.5
        (R/'test-results/wave11-hasumi-mouth-source.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf8')
(R/'test-results/wave11-halo-geometry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('Verified original referenced halo geometry for',len(report),'costumes')
