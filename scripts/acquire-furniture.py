"""Resolve cafe prefab dependencies from verified official cached patch archives."""
import json, pathlib, zipfile, zlib, sys
import UnityPy
R=pathlib.Path(__file__).resolve().parents[1]; W=R/'.assets'
index=json.loads((W/'furniture-index.json').read_text(encoding='utf8'))
cabs=json.loads((W/'cab-index.json').read_text())['cabs']
catalog=json.loads((W/'catalog.json').read_text())
bundles={b['Name']:(p['PackName'],b) for p in catalog['FullPatchPacks'] for b in p['BundleFiles']}
entries=[e for e in index['entries'] if not sys.argv[1:] or e['character'] in sys.argv[1:]]
archives={}; seen={}; missing=set()
def acquire(name):
    if name in seen:return
    seen[name]=[]
    pack,b=bundles[name]
    if pack not in archives:archives[pack]=zipfile.ZipFile(W/'packs'/pack)
    raw=archives[pack].read(name)
    assert len(raw)==b['Size'] and zlib.crc32(raw)==b['Crc'],name
    (W/'selected'/name).write_bytes(raw)
    env=UnityPy.load(raw)
    for asset in list(env.files.values()):
        for f in getattr(asset,'files',{}).values():
            for ref in getattr(f,'externals',[]):
                cab=ref.path.split('/')[-1].lower()
                if cab in cabs:
                    dep=cabs[cab][1]
                    if any(k in dep.lower() for k in ['monoscripts','shader','audio']):continue
                    seen[name].append(dep);acquire(dep)
                elif cab.startswith('cab-'):missing.add(cab)
for entry in entries:
    name=index['prefabs'][entry['icon'].lower()]['bundle']
    acquire(name);print(entry['character'],entry['furnitureId'],'dependencies',len(seen),flush=True)
if '--partners' in sys.argv:
    specs=json.loads((R/'scripts/furniture-partners.json').read_text(encoding='utf8'))
    for prefix,_ in specs.values():
        for name in bundles:
            if name.startswith('character-'+prefix.lower()+'-_mxload-prefabs-'):acquire(name)
for a in archives.values():a.close()
out=W/'furniture-dependencies.json'
prior=json.loads(out.read_text()) if out.exists() else {}
prior.update(seen);out.write_text(json.dumps(prior,indent=2))
(W/'furniture-missing-dependencies.json').write_text(json.dumps(sorted(missing),indent=2))
print('Missing',len(missing),sorted(missing),flush=True)
