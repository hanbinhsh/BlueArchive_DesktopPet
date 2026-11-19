import json,UnityPy
from pathlib import Path
R=Path(__file__).resolve().parents[1];W=R/'.assets';deps=json.loads((W/'band-scene-dependencies.json').read_text())
env=UnityPy.load(*[str(W/'selected'/n) for n in deps['dependencies']]);out=[]
for obj in env.objects:
    if obj.type.name!='GameObject':continue
    go=obj.read()
    if not any(s in go.m_Name.lower() for s in ['stretch','ch0221','natsu']):continue
    tr=next((c.component.read() for c in go.m_Component if c.component.type.name=='Transform'),None);names=[go.m_Name];chain=[]
    while tr:
        chain.append({'name':tr.m_GameObject.read().m_Name,'transform':tr.object_reader.read_typetree()})
        if not tr.m_Father.m_PathID:break
        tr=tr.m_Father.read();names.insert(0,tr.m_GameObject.read().m_Name)
    row={'path':'/'.join(names),'collection':obj.assets_file.name,'pathId':obj.path_id,'chain':chain,'components':[c.component.deref().read_typetree() for c in go.m_Component if c.component.type.name=='MonoBehaviour']};out.append(row);print(row['path'])
(W/'band-scene-usage.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(len(out),'matches')
extra=[]
for obj in env.objects:
    if obj.type.name=='MonoBehaviour':
        d=obj.read_typetree();s=json.dumps(d)
        if 'Stretching' in s or 'CH0221_NonWeapon' in s:extra.append({'collection':obj.assets_file.name,'pathId':obj.path_id,'data':d})
    elif obj.type.name=='GameObject':
        go=obj.read()
        if 'dreammaker_836' in go.m_Name.lower():print('SCENE',go.m_Name,[c.component.type.name for c in go.m_Component])
(W/'band-scene-settings.json').write_text(json.dumps(extra,ensure_ascii=False,indent=2),encoding='utf8')
