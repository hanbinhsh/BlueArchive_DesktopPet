"""Fetch the 6 CH0171_Enemy (Yukino) 3D bundles from FullPatch_031.zip via Range requests with CRC32 verification."""
import json, pathlib, struct, zlib, time
import httpx

W = pathlib.Path('.assets')
BASE = 'https://prod-clientpatch.bluearchiveyostar.com/r96_nvji95owgkbcxlmkb8mi/Windows_PatchPack/'
items = [x for x in json.loads((W / 'yukino-remote.json').read_text('utf8')) if 'spinecharacters' not in x[1].lower()]
targets = {bn: (sz, crc) for pn, bn, sz, crc in items if not (W / 'selected' / bn).exists()}
if not targets:
    print('All CH0171_Enemy bundles already present')
    raise SystemExit(0)

pack = next(p for p in json.loads((W / 'catalog.json').read_text('utf8'))['FullPatchPacks'] if p['PackName'] == 'FullPatch_031.zip')
with httpx.Client(timeout=45, follow_redirects=True) as client:
    def get(start, end):
        for attempt in range(3):
            try:
                r = client.get(BASE + pack['PackName'], headers={'Range': f'bytes={start}-{end}'})
                r.raise_for_status()
                assert r.status_code == 206 and len(r.content) == end - start + 1
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
        if name not in targets:
            continue
        hb = get(header, header + 29)
        lnl, lxl = struct.unpack_from('<HH', hb, 26)
        data_offset = header + 30 + lnl + lxl
        raw = get(data_offset, data_offset + compressed - 1)
        data = zlib.decompress(raw, -15) if method == 8 else raw
        sz, crc = targets.pop(name)
        assert len(data) == sz and zlib.crc32(data) == crc
        (W / 'selected' / name).write_bytes(data)
        print('ACQUIRED', name, len(data), 'bytes CRC OK', flush=True)
assert not targets, f'Missing: {targets}'
print('ALL CH0171_Enemy (Yukino) BUNDLES ACQUIRED')
