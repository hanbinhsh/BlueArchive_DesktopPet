"""Acquire the named official roster, verifying archive and bundle checksums."""
import concurrent.futures
import json
import pathlib
import subprocess
import zipfile
import zlib
import httpx
import sys
import os

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = pathlib.Path(os.environ.get('BA_ASSET_WORK', ROOT / '.assets'))
BASE = os.environ.get('BA_RESOURCE_BASE', 'https://prod-clientpatch.bluearchiveyostar.com/r96_nvji95owgkbcxlmkb8mi/Windows_PatchPack/')
specs = json.loads(pathlib.Path(os.environ.get('BA_ROSTER_SPECS', ROOT/'scripts/roster-wave5.json')).read_text(encoding='utf-8'))
requested = [a for a in sys.argv[1:] if not a.startswith('--')]
if requested: specs = {k:v for k,v in specs.items() if k in requested}
def bundle_keys(prefix):
    prefixes = [prefix.lower()]
    if prefix == 'CH0258': prefixes += ['ch0258_01','ch0258_02']
    return [f'{kind}-{p}-' for p in prefixes for kind in ['characters','character','characteranimation']]
keys = [key for prefix,label in specs.values() for key in bundle_keys(prefix)]
if 'hoshino' in specs: keys += ['assets-_mx-effectsfreezed-material-_mxdependency-materials-']
if 'shiroko_terror' in specs: keys += ['assets-_mx-npcs-en0002-_mxdependency-textures-', 'assets-_mx-characters-ayane_original-_mxdependency-textures-']
if 'suzumi' in specs:
    # Suzumi's override controller inherits the shared prologue controller.
    keys += ['prologdepengroup-assets-_mx-addressableasset-character-_mxprolog-2025-07-02_assets_all_1152943758.bundle',
             'prologdepengroup-assets-_mx-program-animators-_mxprolog-2026-05-29_assets_all_1647538028.bundle']
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
evidence_path = WORK / (os.environ.get('BA_ACQUISITION_NAME', 'wave5')+'-acquisition.json')
old = json.loads(evidence_path.read_text()) if evidence_path.exists() else []
merged = {p['url']:p for p in old}
for p in evidence:
    prior = merged.get(p['url'],{}).get('bundles',[])
    p['bundles'] = list({b['Name']:b for b in prior+p['bundles']}.values())
    merged[p['url']] = p
evidence_path.write_text(json.dumps(list(merged.values()), indent=2), encoding='utf-8')
if '--assets-only' in sys.argv: sys.exit(0)
for name, (prefix,label) in specs.items():
    key = prefix.lower()
    files = sorted(p for p in (WORK / 'selected').glob('*.bundle') if any(k in p.name for k in bundle_keys(prefix)))
    request = {'schema_version': 0, 'operation': 'export_primary_content', 'inputs': [{'path': str(p), 'node_id': p.name, 'target': True} for p in files], 'output_directory': str(WORK / 'exported' / name), 'concurrency': 2}
    own = {item['path'] for item in request['inputs']}
    request['inputs'] += [{'path':str(p),'node_id':p.name,'target':False} for p in (WORK/'selected').glob('*.bundle') if str(p) not in own and any(k in p.name for k in ['-materials-','-textures-','-meshes-','-animatorcontrollers-','-animationclips-','_mx-program-animators-','prologdepengroup-assets-_mx-addressableasset-character-'])]
    request_path = WORK / f'{name}-request.json'
    request_path.write_text(json.dumps(request), encoding='utf-8')
    with (WORK / f'{name}-export.log').open('w', encoding='utf-8') as log:
        dotnet = ROOT / '.cache/dotnet/dotnet.exe'
        exporter = ROOT / '.assets' / 'euler-exporter' / 'AssetRipperExporter.dll'
        if not exporter.exists(): raise RuntimeError('Build scripts/build-euler-exporter.py first')
        result = subprocess.run([str(dotnet) if dotnet.exists() else 'dotnet', str(exporter), str(request_path), str(WORK / f'{name}-result.json')], stdout=log, stderr=subprocess.STDOUT)
    print(name, 'export', result.returncode, flush=True)
    if result.returncode: raise RuntimeError(f'Export failed for {name}; see {name}-export.log')
