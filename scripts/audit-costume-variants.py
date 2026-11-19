"""Compare source mesh/material identities of installed and alternate prefabs.

Uses verified cached archives. Source identifiers are not costume labels.
The report keeps visibility and transforms separate from shared geometry.
"""
import json, pathlib, re, zipfile, zlib
import httpx
import UnityPy

R=pathlib.Path(__file__).resolve().parents[1]
W=R/'.assets'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
catalog=read(W/'catalog.json')
coverage=read(R/'test-results/costume-coverage.json')
specs={'serika':['Serika_Original','芹香'], 'serika_newyear':['Serika_Newyear','芹香'],
       'junko':['Zunko_Original','纯子'],'junko_newyear':['CH0192','纯子'],
       'serika_swimsuit':['CH0189','芹香'],'plana':['Plana','普拉娜']}
for file in ['roster-expansion.json','roster-wave3.json','roster-wave4.json','roster-wave5.json','roster-wave6.json']:
    specs.update(read(R/'scripts'/file))
codes={v[0].lower() for v in specs.values()}
codes|={'np0009','np0267','np0268','toki_cnc_mg_boss','ch0258_01','ch0258_02'}
names={row['sourceName'].lower() for row in coverage['characters']}|{'zunko','plana'}
def related(name):
    name=name.lower()
    return any(re.search(r'(?<![a-z0-9])'+re.escape(code)+r'(?![a-z0-9])',name) for code in codes|names)

stage=W/'costume-variants'
stage.mkdir(exist_ok=True)
evidence=[]
for pack in catalog['FullPatchPacks']:
    selected=[b for b in pack['BundleFiles'] if '-prefabs-' in b['Name'] and
              not any(s in b['Name'] for s in ['spine','cafe-misc','skillcut']) and
              (related(b['Name']) or any(s in b['Name'] for s in [
                  'field-npc-','field-player-','field-character-','assets-_mx-field-characters-','assets-_mx-field-npcs-']))]
    if not selected:continue
    archive=W/'packs'/pack['PackName']
    if not archive.exists():
        print('Downloading candidate source archive',pack['PackName'],pack['PackSize'],flush=True)
        with httpx.stream('GET','https://prod-clientpatch.bluearchiveyostar.com/r96_nvji95owgkbcxlmkb8mi/Windows_PatchPack/'+pack['PackName'],timeout=120) as response:
            response.raise_for_status()
            with archive.open('wb') as target:
                for chunk in response.iter_bytes():target.write(chunk)
        raw=archive.read_bytes()
        assert len(raw)==pack['PackSize'] and zlib.crc32(raw)==pack['Crc']
    with zipfile.ZipFile(archive) as z:
        for b in selected:
            raw=z.read(b['Name'])
            assert len(raw)==b['Size'] and zlib.crc32(raw)==b['Crc'],b['Name']
            (stage/b['Name']).write_bytes(raw)
            evidence.append({'pack':pack['PackName'],'bundle':b})

env=UnityPy.load(*map(str,stage.glob('*.bundle')))
def pointer(p):
    if not p or not p.m_PathID:return None
    file=p.assetsfile
    cab=file.externals[p.m_FileID-1].path.replace('\\','/').split('/')[-1] if p.m_FileID else file.name
    return [cab.lower(),p.m_PathID]
def vec(v):return [v.x,v.y,v.z]+([v.w] if hasattr(v,'w') else [])
def walk(go,parent=True):
    active=parent and bool(go.m_IsActive)
    components=[c.component.read() for c in go.m_Component]
    transform=next(c for c in components if c.object_reader.type.name=='Transform')
    rows=[]
    for c in components:
        kind=c.object_reader.type.name
        if kind not in ['SkinnedMeshRenderer','MeshRenderer']:continue
        mesh=getattr(c,'m_Mesh',None)
        if mesh is None:
            filt=next((v for v in components if v.object_reader.type.name=='MeshFilter'),None)
            mesh=filt.m_Mesh if filt else None
        if not mesh or not mesh.m_PathID:continue
        rows.append({'node':go.m_Name,'type':kind,'mesh':pointer(mesh),
                     'materials':[pointer(p) for p in c.m_Materials],
                     'enabled':bool(c.m_Enabled),'active':active,
                     'position':vec(transform.m_LocalPosition),'rotation':vec(transform.m_LocalRotation),
                     'scale':vec(transform.m_LocalScale)})
    for child in transform.m_Children:rows+=walk(child.read().m_GameObject.read(),active)
    return rows
roots=[]
for obj in env.objects:
    if obj.type.name!='GameObject':continue
    go=obj.read()
    if not related(go.m_Name):continue
    transform=next((c.component.read() for c in go.m_Component if c.component.deref().type.name=='Transform'),None)
    if not transform or transform.m_Father.m_PathID:continue
    renderers=walk(go)
    if renderers:
        roots.append({'name':go.m_Name,'source':obj.assets_file.name,'pathId':obj.path_id,'renderers':renderers})
roots.sort(key=lambda x:x['name'].lower())
(R/'test-results/costume-source-variants.json').write_text(json.dumps({'roots':roots,'acquisition':evidence},ensure_ascii=False,indent=2),encoding='utf8')
print('Verified bundles:',len(evidence),'related prefab roots:',len(roots))
for root in roots:
    print(root['name'],len(root['renderers']))
