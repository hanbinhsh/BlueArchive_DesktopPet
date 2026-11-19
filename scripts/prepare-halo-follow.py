"""Read original HaloRoot follow components into the self-contained GLBs."""
import pathlib, json, UnityPy, os
from glb import load, save
ROOT = pathlib.Path(__file__).resolve().parents[1]
source_dirs = [pathlib.Path(p) for p in json.loads(os.environ.get('BA_SOURCE_DIRS', '[]'))] or [ROOT/'.assets/selected']
source_files = {p.name:p for folder in source_dirs for p in folder.glob('*.bundle')}
env = globals().get('source_environment') or UnityPy.load(*map(str, source_files.values()))
sources = {}
prefixes = {'serika':'Serika_Original','serika_newyear':'Serika_Newyear','junko':'Zunko_Original','junko_newyear':'CH0192','serika_swimsuit':'CH0189'}
prefixes.update({k:v[0] for k,v in json.loads((ROOT/'scripts/roster-expansion.json').read_text(encoding='utf-8')).items() if (ROOT/'characters'/k/'model.glb').exists()})
prefixes.update({k:v[0] for k,v in json.loads((ROOT/'scripts/roster-wave3.json').read_text(encoding='utf-8')).items() if (ROOT/'characters'/k/'model.glb').exists()})
prefixes.update({k:v[0] for k,v in json.loads((ROOT/'scripts/roster-wave4.json').read_text(encoding='utf-8')).items() if (ROOT/'characters'/k/'model.glb').exists()})
prefixes.update({k:v[0] for k,v in json.loads((ROOT/'scripts/roster-wave5.json').read_text(encoding='utf-8')).items() if (ROOT/'characters'/k/'model.glb').exists()})
prefixes.update({k:v[0] for k,v in json.loads((ROOT/'scripts/roster-wave6.json').read_text(encoding='utf-8')).items() if (ROOT/'characters'/k/'model.glb').exists()})
if 'toki' in prefixes: prefixes['toki'] = 'CH0187_CafeOnly'
prefixes.update({k:v[0] for k,v in json.loads((ROOT/'scripts/roster-wave7.json').read_text(encoding='utf-8')).items() if (ROOT/'characters'/k/'model.glb').exists()})
if 'hoshino_battle' in prefixes: prefixes['hoshino_battle'] = 'CH0258_01'
output=pathlib.Path(os.environ.get('BA_CHARACTER_OUTPUT', ROOT/'characters'))
if os.environ.get('BA_ROSTER_SPECS'): prefixes={k:v[0] for k,v in json.loads(pathlib.Path(os.environ['BA_ROSTER_SPECS']).read_text(encoding='utf8')).items() if (output/k/'model.glb').exists()}
if os.environ.get('BA_ROSTER_PROFILES'):
    profiles=json.loads(pathlib.Path(os.environ['BA_ROSTER_PROFILES']).read_text(encoding='utf8'))
    prefixes={k:profiles.get(k,{}).get('prefabName',v) for k,v in prefixes.items()}
for obj in env.objects:
    if obj.type.name != 'MonoBehaviour': continue
    data = obj.read_typetree()
    if 'FollowTarget' not in data or 'TargetRelativePosition' not in data: continue
    go = obj.read().m_GameObject.read()
    transform = next(c.component.read() for c in go.m_Component if c.component.deref().type.name=='Transform')
    if not transform.m_Father.m_PathID: continue
    parent = transform.m_Father.read().m_GameObject.read().m_Name
    if parent not in prefixes.values(): continue
    target = UnityPy.classes.PPtr(**data['FollowTarget'],assetsfile=obj.assets_file).read().m_GameObject.read().m_Name
    sources[parent] = {'node':go.m_Name,'target':target,'data':data}
report = {}
for pack,prefix in prefixes.items():
    if prefix not in sources and pack in json.loads(os.environ.get('BA_ALLOW_NO_HALO','[]')):
        doc,_=load(output/pack/'model.glb')
        assert not any('halo' in n.get('name','').lower() for n in doc['nodes']),pack
        assert not doc['scenes'][0].get('extras',{}).get('BA_halo_follow'),pack
        report[pack]={'absent':True,'reason':'Original prefab has no halo node or halo-follow component'}
        continue
    source=sources[prefix]; data=source['data']
    path=output/pack/'model.glb';doc,binary=load(path)
    nodes={n['name']:i for i,n in enumerate(doc['nodes'])}
    def vec(key):
        v=data[key];return [-v['x'],v['y'],v['z']]
    q=data['TargetRelativeRotation']
    follow={'node':nodes[source['node']],'target':nodes[source['target']],
        'offset':vec('TargetRelativePosition'),'rotation':[q['x'],-q['y'],-q['z'],q['w']],
        'minOffset':[-data['ClampMaxOffset']['x'],data['ClampMinOffset']['y'],data['ClampMinOffset']['z']],
        'maxOffset':[-data['ClampMinOffset']['x'],data['ClampMaxOffset']['y'],data['ClampMaxOffset']['z']],
        'positionPower':data['FollowPositionPower'],'rotationPower':data['FollowRotationPower'],'fixYRotation':bool(data['FixYRotation'])}
    if os.environ.get('BA_VERIFY_HALOS'):
        assert doc['scenes'][0]['extras']['BA_halo_follow']==follow,pack
    else:
        doc['scenes'][0].setdefault('extras',{})['BA_halo_follow']=follow
        save(path,doc,binary)
    report[pack]=source
(ROOT/os.environ.get('BA_HALO_REPORT','test-results/furniture-partner-halos.json' if os.environ.get('BA_ROSTER_SPECS') else 'test-results/halo-source.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
print('Preserved official halo follow parameters:',list(report))
