"""Acquire Wave 20 character bundles from verified official cached patch archives."""
import json, pathlib, zipfile, zlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = ROOT / '.assets'
specs = json.loads((ROOT / 'scripts/roster-wave20.json').read_text(encoding='utf-8'))
catalog = json.loads((WORK / 'catalog.json').read_text(encoding='utf-8'))

keys = [f'{kind}-{prefix.lower()}-' for prefix, _ in specs.values() for kind in ['characters', 'character', 'characteranimation']]
packs = [p for p in catalog['FullPatchPacks'] if any(any(k in b['Name'] for k in keys) for b in p['BundleFiles'])]

missing_packs = []
for pack in packs:
    target = WORK / 'packs' / pack['PackName']
    if not target.exists() or target.stat().st_size != pack['PackSize']:
        missing_packs.append(pack['PackName'])

if missing_packs:
    print('MISSING PACKS (need download):', missing_packs)
    sys.exit(2)

extracted = 0
skipped = 0
evidence = []
for pack in packs:
    bundles = [b for b in pack['BundleFiles'] if any(k in b['Name'] for k in keys)]
    target = WORK / 'packs' / pack['PackName']
    with zipfile.ZipFile(target) as archive:
        for b in bundles:
            dest = WORK / 'selected' / b['Name']
            if dest.exists() and dest.stat().st_size == b['Size'] and zlib.crc32(dest.read_bytes()) == b['Crc']:
                skipped += 1
                continue
            raw = archive.read(b['Name'])
            assert len(raw) == b['Size'] and zlib.crc32(raw) == b['Crc'], b['Name']
            dest.write_bytes(raw)
            extracted += 1
    evidence.append({'pack': pack['PackName'], 'crc32': pack['Crc'], 'bundleCount': len(bundles)})

(WORK / 'wave20-acquisition.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
print(f'Verified {len(packs)} packs: extracted {extracted} new bundles, {skipped} already present in .assets/selected/')
