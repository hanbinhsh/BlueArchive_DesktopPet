"""Fetch only catalog packs containing the candidate characters; retain matching bundles."""
import concurrent.futures
import json
import pathlib
import zipfile
import zlib
import httpx
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = ROOT / '.assets'
BASE = 'https://prod-clientpatch.bluearchiveyostar.com/r96_nvji95owgkbcxlmkb8mi/Windows_PatchPack/'
WORK.mkdir(exist_ok=True)
if not (WORK / 'catalog.json').exists():
    response = httpx.get(BASE + 'BundlePackingInfo.json', timeout=60)
    response.raise_for_status()
    (WORK / 'catalog.json').write_bytes(response.content)
catalog = json.loads((WORK / 'catalog.json').read_text())
keys = ['serika_original', 'npcs-plana', 'characters-_mxcommon-_mxdependency-textures-2025-07-02', 'characters-_mxcommon-_mxprolog-2025-07-02']
if '--newyear' in sys.argv:
    keys = ['assets-_mx-characters-serika_newyear', 'cafe-characteranimation-serika_newyear', 'character-serika_newyear']
packs = [p for p in catalog['FullPatchPacks'] if any(any(k in b['Name'] for k in keys) for b in p['BundleFiles'])]
(WORK / 'packs').mkdir(exist_ok=True)
(WORK / 'selected').mkdir(exist_ok=True)

def fetch(pack):
    target = WORK / 'packs' / pack['PackName']
    if not target.exists() or target.stat().st_size != pack['PackSize']:
        print('Downloading', pack['PackName'], pack['PackSize'], flush=True)
        with httpx.stream('GET', BASE + pack['PackName'], timeout=120, follow_redirects=True) as response:
            response.raise_for_status()
            with target.open('wb') as stream:
                for chunk in response.iter_bytes():
                    stream.write(chunk)
    data = target.read_bytes()
    if len(data) != pack['PackSize'] or zlib.crc32(data) != pack['Crc']:
        raise ValueError(f'Archive checksum mismatch: {target.name}')
    selected = [b for b in pack['BundleFiles'] if any(k in b['Name'] for k in keys)]
    with zipfile.ZipFile(target) as archive:
        for bundle in selected:
            name = bundle['Name']
            data = archive.read(name)
            if len(data) != bundle['Size'] or zlib.crc32(data) != bundle['Crc']:
                raise ValueError(f'Bundle checksum mismatch: {name}')
            (WORK / 'selected' / pathlib.Path(name).name).write_bytes(data)
    print('Verified', target.name, len(selected), 'bundles', flush=True)
    return {'url': BASE + target.name, 'crc32': pack['Crc'], 'bundles': selected}

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    evidence = list(executor.map(fetch, packs))
(WORK / ('newyear-acquisition.json' if '--newyear' in sys.argv else 'acquisition.json')).write_text(json.dumps(evidence, indent=2))
