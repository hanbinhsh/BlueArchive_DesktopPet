"""Extract verified official JP r96 bundles for all 16 Wave 21 outfits from cached local packs."""
import json, pathlib, zipfile, zlib

R = pathlib.Path(__file__).resolve().parents[1]
W = R / '.assets'
catalog = json.loads((W / 'catalog.json').read_text('utf8'))
specs = json.loads((R / 'scripts/roster-wave21.json').read_text('utf8'))
prefixes = sorted({p.lower() for p, _ in specs.values()})

needed = {}
for pack in catalog['FullPatchPacks']:
    for b in pack['BundleFiles']:
        n = b['Name'].lower()
        if 'audio' in n or 'spine' in n:
            continue
        if any(
            n.startswith(f'character-{p}-')
            or n.startswith(f'assets-_mx-characters-{p}-')
            or n.startswith(f'cafe-characteranimation-{p}-')
            for p in prefixes
        ):
            needed.setdefault(pack['PackName'], []).append(b)

out = W / 'selected'
out.mkdir(parents=True, exist_ok=True)
extracted = 0
already = 0
missing_packs = []
for pack_name, items in sorted(needed.items()):
    zp = W / 'packs' / pack_name
    if not zp.exists():
        missing_packs.append((pack_name, len(items)))
        continue
    with zipfile.ZipFile(zp) as zf:
        for b in items:
            dst = out / b['Name']
            if dst.exists() and dst.stat().st_size == b['Size']:
                already += 1
                continue
            raw = zf.read(b['Name'])
            assert len(raw) == b['Size'] and zlib.crc32(raw) == b['Crc'], b['Name']
            dst.write_bytes(raw)
            extracted += 1

print(f'Verified {len(needed)} packs: extracted {extracted} new bundles, {already} already present in .assets/selected/')
if missing_packs:
    print('MISSING LOCAL PACKS:', missing_packs)
    raise SystemExit(1)
