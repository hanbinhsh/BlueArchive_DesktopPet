"""Index official cafe prefabs and cached dependency headers; no game-wide download."""
import json, pathlib, zipfile, zlib, os
import UnityPy
from importlib.machinery import SourceFileLoader

R = pathlib.Path(__file__).resolve().parents[1]
W = R/'.assets'
cab_names = SourceFileLoader('find_cab', str(R/'scripts/find-cab.py')).load_module().cab_names
catalog = json.loads((W/'catalog.json').read_text())
bundles = {b['Name']:(p['PackName'],b) for p in catalog['FullPatchPacks'] for b in p['BundleFiles']}
index_path = W/'cab-index.json'
index = json.loads(index_path.read_text()) if index_path.exists() else {}
done = set(index.get('packs', [])); cabs = index.get('cabs', {})
for pack in sorted((W/'packs').glob('*.zip')):
    if pack.name in done: continue
    with zipfile.ZipFile(pack) as z:
        for name in z.namelist():
            if not name.endswith('.bundle'): continue
            with z.open(name) as f: raw = f.read(16384)
            try: names = cab_names(raw)
            except ValueError: names = cab_names(z.read(name))
            for cab in names:
                if not cab.endswith('.ress') and not cab.endswith('.resource'): cabs[cab] = [pack.name,name]
    done.add(pack.name)
    index_path.write_text(json.dumps({'packs':sorted(done),'cabs':cabs}))
    print('Indexed',pack.name,flush=True)

students = json.loads((W/os.environ.get('BA_STUDENTS_SNAPSHOT','students-audit-2026-10-21.json')).read_text(encoding='utf8'))
furniture = json.loads((W/'furniture-cn.json').read_text(encoding='utf8'))
aliases = {'koyuki_pajama':'koyuki_pajamas','toki_bunnygirl':'toki_bunny','hoshino_battle_tank':'hoshino_battle','hoshino_battle_dealer':'hoshino_battle'}
roster = {p.parent.name:json.loads(p.read_text(encoding='utf8')) for p in (R/'characters').glob('*/character.json')}
entries = {}
for s in students.values():
    pack = aliases.get(s['PathName'],s['PathName'])
    if pack not in roster or not s['IsReleased'][0]: continue
    for fid,variant in s.get('FurnitureInteraction',[[]])[0]:
        key=f'{pack}:{fid}:{variant}'
        entries[key] = {'character':pack,'studentId':s['Id'],'devName':s['DevName'],'furnitureId':fid,'variant':variant,'name':furniture[str(fid)]['Name'],'icon':furniture[str(fid)]['Icon']}
prefabs={}
for pack in catalog['FullPatchPacks']:
    selected=[b for b in pack['BundleFiles'] if 'cafe-_mxload-prefabs-' in b['Name']]
    if not selected or not (W/'packs'/pack['PackName']).exists():continue
    with zipfile.ZipFile(W/'packs'/pack['PackName']) as z:
        for b in selected:
            raw=z.read(b['Name']);env=UnityPy.load(raw)
            for obj in list(env.objects):
                if obj.type.name!='AssetBundle':continue
                for name,_ in obj.read().m_Container:
                    prefabs[pathlib.PurePosixPath(name).stem.lower()]={'pack':pack['PackName'],'bundle':b['Name']}
    print('Prefab index',pack['PackName'],len(prefabs),flush=True)
# The icon is a thumbnail variant; the official PlayableDirector uses the base prefab.
for entry in entries.values():
    if entry['icon']=='my_event070_chair_01' and 'my_event070_chair' in prefabs:entry['icon']='my_event070_chair'
(W/'furniture-index.json').write_text(json.dumps({'entries':list(entries.values()),'prefabs':prefabs},ensure_ascii=False,indent=2),encoding='utf8')
print('Interactions',len(entries),'missing prefabs',sorted({e['icon'] for e in entries.values() if e['icon'].lower() not in prefabs}),flush=True)
