"""Find a missing CAB by reading only material members with HTTP byte ranges."""
import concurrent.futures, io, json, pathlib, struct, threading, zipfile, zlib
import httpx, UnityPy, time, re

W = pathlib.Path('.assets')
BASE = 'https://prod-clientpatch.bluearchiveyostar.com/r96_nvji95owgkbcxlmkb8mi/Windows_PatchPack/'
WANTED = {'cab-e9f439eb6a52b051cda6738233134061','cab-5dba4336fdb2f6f32c2b8a8006c41b49','cab-16d373fbdf45218dcb9e4f1b045a2a1c','cab-2eb2ef5b7bfcab02eed64fafa5f7ce1b','cab-e1d510b765bacefde4b3463509966c23'}
matched=set()
completed=set()
found = threading.Event()

def scan(pack):
    if found.is_set() or pack['PackName'] in completed: return
    names = {b['Name']: b for b in pack['BundleFiles'] if '-materials-' in b['Name']}
    if not names or (W/'packs'/pack['PackName']).exists(): return
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        url = BASE + pack['PackName']
        def get(start, end):
            for attempt in range(4):
                try:
                    response = client.get(url, headers={'Range': f'bytes={start}-{end}'})
                    break
                except httpx.TransportError:
                    if attempt==3:raise
                    time.sleep(attempt+1)
            response.raise_for_status()
            if response.status_code != 206 or len(response.content) != end-start+1:
                raise RuntimeError('Server did not honor range')
            return response.content
        size = pack['PackSize']; start = max(0, size-1048576)
        tail = get(start, size-1)
        # A sparse local buffer provides the central directory without fetching assets.
        stream = io.BytesIO(); stream.seek(start); stream.write(tail)
        with zipfile.ZipFile(stream) as archive:
            infos = [i for i in archive.infolist() if i.filename in names]
        for info in infos:
            if found.is_set(): return
            raw = get(info.header_offset, info.header_offset+30+len(info.filename.encode())+info.compress_size+255)
            name_len, extra_len = struct.unpack_from('<HH', raw, 26)
            offset = 30+name_len+extra_len
            payload = raw[offset:offset+info.compress_size]
            data = zlib.decompress(payload, -15) if info.compress_type == 8 else payload
            expected = names[info.filename]
            assert len(data) == expected['Size'] and zlib.crc32(data) == expected['Crc']
            env = UnityPy.load(data)
            hits={n.lower() for bundle in env.files.values() for n in bundle.files}&WANTED
            if hits:
                (W/'selected'/info.filename).write_bytes(data)
                (W/'cafe-extra-material-acquisition.json').write_text(json.dumps({'url':url,'bundle':expected},indent=2))
                matched.update(hits)
                print('FOUND',pack['PackName'],info.filename,hits,flush=True)
                if matched==WANTED:found.set();return
        print('Scanned material headers',pack['PackName'],len(infos),flush=True)

packs = json.loads((W/'catalog.json').read_text())['FullPatchPacks']
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    for result in pool.map(scan, packs): pass
if not found.is_set(): print('Material CAB not found')
