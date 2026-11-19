"""Acquire only Field 833 bedroom and its catalog-resolved dependencies."""
import json,zipfile,zlib,httpx,UnityPy,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];W=R/'.assets'
catalog=json.loads((W/'catalog.json').read_text());cabs=json.loads((W/'cab-index.json').read_text())['cabs']
bundles={b['Name']:(p,b) for p in catalog['FullPatchPacks'] for b in p['BundleFiles']}
archives={};seen={};missing=set()
def acquire(name):
    if name in seen:return
    seen[name]=[];pack,b=bundles[name];path=W/'packs'/pack['PackName']
    if pack['PackName'] not in archives:
        if not path.exists() or path.stat().st_size!=pack['PackSize']:
            print('Downloading',path.name,flush=True)
            with httpx.stream('GET','https://prod-clientpatch.bluearchiveyostar.com/r96_nvji95owgkbcxlmkb8mi/Windows_PatchPack/'+path.name,timeout=180) as response:
                response.raise_for_status()
                with path.open('wb') as f:
                    for chunk in response.iter_bytes():f.write(chunk)
        raw=path.read_bytes();assert len(raw)==pack['PackSize'] and zlib.crc32(raw)==pack['Crc']
        archives[pack['PackName']]=zipfile.ZipFile(path)
    raw=archives[pack['PackName']].read(name);assert len(raw)==b['Size'] and zlib.crc32(raw)==b['Crc']
    (W/'selected'/name).write_bytes(raw)
    env=UnityPy.load(raw)
    for asset in env.files.values():
        for f in getattr(asset,'files',{}).values():
            for ref in getattr(f,'externals',[]):
                cab=ref.path.split('/')[-1].lower()
                if cab in cabs:
                    dep=cabs[cab][1]
                    if any(k in dep.lower() for k in ['monoscripts','shader','audio']):continue
                    seen[name].append(dep);acquire(dep)
                elif cab.startswith('cab-'):missing.add(cab)
roots=[n for n in bundles if 'field833-field_833_zone01-' in n or 'field-scenes-artlevel-field833-_mxload-scenes-' in n or 'field-scenes-designlevel-field833-_mxload-prefabs-' in n]
if '--band' in sys.argv:roots=[n for n in bundles if 'minigame-dreammaker-artlevel-_mxload-scenes-' in n or 'minigame-dreammaker-_mxload-prefabs-' in n]
if '--textures' in sys.argv:roots=[n for n in bundles if 'assets-_mx-field-scenes-_mxdependency-textures-' in n]
for root in roots:acquire(root)
for a in archives.values():a.close()
(W/('bedroom-texture-dependencies.json' if '--textures' in sys.argv else 'band-scene-dependencies.json' if '--band' in sys.argv else 'bedroom-dependencies.json')).write_text(json.dumps({'roots':roots,'dependencies':seen,'missing':sorted(missing)},indent=2),encoding='utf8')
print('Bedroom dependencies:',len(seen),'unresolved:',len(missing),flush=True)
