"""Fetch the 5 Wave 17 FX dependency bundles referenced by remote-cab-headers.json with CRC32 check."""
import json, pathlib, struct, zlib, time
import httpx

W = pathlib.Path('.assets')
BASE = 'https://prod-clientpatch.bluearchiveyostar.com/r96_nvji95owgkbcxlmkb8mi/Windows_PatchPack/'
targets = {
    'assets-_mx-npcs-haunted_king-_mxdependency-textures-2025-07-02_assets_all_829095610.bundle',
    'assets-_mx-npcs-en0008_original_01-_mxdependency-textures-2025-07-02_assets_all_592235795.bundle',
    'assets-_mx-scenes-battle-zennosento-_mxdependency-textures-2026-01-04_assets_all_1475537062.bundle',
    'assets-_mx-npcs-armoredcar_wakamo_mg-_mxdependency-materials-2025-07-02_assets_all_1332350391.bundle',
    'assets-_mx-npcs-en0022_original_02-_mxdependency-textures-2026-04-27_assets_all_3424774315.bundle',
}
targets = {t for t in targets if not (W / 'selected' / t).exists()}
if not targets:
    print('All 5 bundles already present in .assets/selected')
    raise SystemExit(0)

packs = json.loads((W / 'catalog.json').read_text('utf8'))['FullPatchPacks']
plan = []
for pack in packs:
    hits = {b['Name']: b for b in pack['BundleFiles'] if b['Name'] in targets}
    if hits:
        plan.append((pack, hits))
print('Packs to fetch from:', [(p['PackName'], list(h)) for p, h in plan], flush=True)

with httpx.Client(timeout=45, follow_redirects=True) as client:
    for pack, hits in plan:
        def get(start, end):
            for attempt in range(3):
                try:
                    r = client.get(BASE + pack['PackName'], headers={'Range': f'bytes={start}-{end}'})
                    r.raise_for_status()
                    if r.status_code != 206 or len(r.content) != end - start + 1:
                        raise ValueError('Invalid range')
                    return r.content
                except httpx.HTTPError:
                    if attempt == 2:
                        raise
                    time.sleep(attempt + 1)
        size = pack['PackSize']
        start = max(0, size - 65536)
        tail = get(start, size - 1)
        end = tail.rfind(b'PK\x05\x06')
        length, offset = struct.unpack_from('<II', tail, end + 12)
        directory = tail[offset - start:offset - start + length] if offset >= start else get(offset, offset + length - 1)
        p = 0
        while p < len(directory):
            assert directory[p:p + 4] == b'PK\x01\x02'
            method = struct.unpack_from('<H', directory, p + 10)[0]
            compressed = struct.unpack_from('<I', directory, p + 20)[0]
            nl, xl, cl = struct.unpack_from('<HHH', directory, p + 28)
            header = struct.unpack_from('<I', directory, p + 42)[0]
            name = directory[p + 46:p + 46 + nl].decode()
            p += 46 + nl + xl + cl
            if name not in hits:
                continue
            hb = get(header, header + 29)
            lnl, lxl = struct.unpack_from('<HH', hb, 26)
            data_offset = header + 30 + lnl + lxl
            raw = get(data_offset, data_offset + compressed - 1)
            data = zlib.decompress(raw, -15) if method == 8 else raw
            expected = hits[name]
            assert len(data) == expected['Size'] and zlib.crc32(data) == expected['Crc'], (name, len(data), expected)
            (W / 'selected' / name).write_bytes(data)
            targets.discard(name)
            print('ACQUIRED', name, len(data), 'bytes CRC OK', flush=True)
assert not targets, f'Still missing: {targets}'
print('ALL 5 FX DEPENDENCY BUNDLES ACQUIRED AND VERIFIED')
