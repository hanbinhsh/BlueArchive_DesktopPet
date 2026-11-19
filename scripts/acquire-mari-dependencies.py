"""Acquire the named official roster, verifying archive and bundle checksums."""
import concurrent.futures
import json
import pathlib
import subprocess
import zipfile
import zlib
import httpx

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = ROOT / '.assets'
BASE = 'https://prod-clientpatch.bluearchiveyostar.com/r96_nvji95owgkbcxlmkb8mi/Windows_PatchPack/'
specs = json.loads((ROOT/'scripts/roster-wave3.json').read_text(encoding='utf-8'))
keys = ['assets-_mx-characters-ch0184-_mxdependency-textures-', 'assets-_mx-characters-ch0184-_mxdependency-materials-']
catalog = json.loads((WORK / 'catalog.json').read_text(encoding='utf-8'))

def acquire(pack):
    bundles = [b for b in pack['BundleFiles'] if any(k in b['Name'] for k in keys)]
    target = WORK / 'packs' / pack['PackName']
    if not target.exists() or target.stat().st_size != pack['PackSize']:
        print('Downloading', target.name, flush=True)
        with httpx.stream('GET', BASE + target.name, timeout=180, follow_redirects=True) as response:
            response.raise_for_status()
            with target.open('wb') as stream:
                for chunk in response.iter_bytes(): stream.write(chunk)
    raw = target.read_bytes()
    assert len(raw) == pack['PackSize'] and zlib.crc32(raw) == pack['Crc'], target.name
    with zipfile.ZipFile(target) as archive:
        for b in bundles:
            raw = archive.read(b['Name'])
            assert len(raw) == b['Size'] and zlib.crc32(raw) == b['Crc'], b['Name']
            (WORK / 'selected' / b['Name']).write_bytes(raw)
    print('Verified', target.name, len(bundles), flush=True)
    return {'url': BASE + target.name, 'crc32': pack['Crc'], 'bundles': bundles}

packs = [p for p in catalog['FullPatchPacks'] if any(any(k in b['Name'] for k in keys) for b in p['BundleFiles'])]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    evidence = list(pool.map(acquire, packs))
(WORK / 'mari-dependency-acquisition.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
