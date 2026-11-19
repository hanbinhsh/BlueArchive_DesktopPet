import json,re,UnityPy
from pathlib import Path
R=Path(__file__).resolve().parents[1];W=R/'.assets'
deps=json.loads((W/'bedroom-dependencies.json').read_text())
env=UnityPy.load(*[str(W/'selected'/n) for n in deps['dependencies']])
rows=[]
def treepath(go):
    names=[go.m_Name];tr=next((c.component.read() for c in go.m_Component if c.component.type.name=='Transform'),None)
    while tr and tr.m_Father.m_PathID:
        tr=tr.m_Father.read();names.insert(0,tr.m_GameObject.read().m_Name)
    return '/'.join(names)
for obj in env.objects:
    if obj.type.name!='GameObject':continue
    go=obj.read()
    if not re.search(r'833.*(?:bed|windowsofa)|(?:bed|windowsofa).*833',go.m_Name,re.I):continue
    components=[]
    for c in go.m_Component:
        o=c.component.deref();d=o.read_typetree();kind=o.type.name
        if kind not in ['MeshRenderer','SkinnedMeshRenderer','MeshFilter']:components.append({'type':kind,'data':d})
    rows.append({'name':go.m_Name,'path':treepath(go),'collection':obj.assets_file.name,'pathId':obj.path_id,'components':components})
report=W/'bedroom-source.json';report.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
for r in rows:print(r['path'],r['collection'],r['pathId'],[c['type'] for c in r['components']])
print('Matches',len(rows))
