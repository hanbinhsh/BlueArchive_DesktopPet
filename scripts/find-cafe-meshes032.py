"""Find a missing CAB by reading only material members with HTTP byte ranges."""
import concurrent.futures, io, json, pathlib, struct, threading, zipfile, zlib
import httpx, UnityPy, time, re

W = pathlib.Path('.assets')
BASE = 'https://prod-clientpatch.bluearchiveyostar.com/r96_nvji95owgkbcxlmkb8mi/Windows_PatchPack/'
audit={'unresolvedReferences':json.loads(pathlib.Path('.assets/cafe-fx-audit032/source.json').read_text('utf8'))['errors']}
from importlib.machinery import SourceFileLoader
cab_names=SourceFileLoader('cab','scripts/find-cab.py').load_module().cab_names
WANTED={m for e in audit['unresolvedReferences'] for m in re.findall(r'cab-[a-f0-9]+',str(e))}
WANTED-=set(json.loads((W/'local-cab-index.json').read_text('utf8'))['cabs'])
index_lock=threading.Lock()
matched=set()
completed=set()
found = threading.Event()

def scan(pack):
    if found.is_set() or pack['PackName'] in completed: return
    names = {b['Name']: b for b in pack['BundleFiles'] if '-meshes-' in b['Name'] or '-shaders-' in b['Name']}
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
            raw = get(info.header_offset,min(size-1,info.header_offset+30+len(info.filename.encode())+min(info.compress_size,65536)+255))
            name_len, extra_len = struct.unpack_from('<HH', raw, 26)
            offset = 30+name_len+extra_len
            payload = raw[offset:offset+info.compress_size]
            try:
                header=zlib.decompressobj(-15).decompress(payload,16384) if info.compress_type==8 else payload[:16384]
                hits=set(cab_names(header))&WANTED
            except (ValueError,zlib.error,IndexError):
                print('Header unavailable',info.filename,flush=True);continue
            if not hits:continue
            if len(payload)<info.compress_size:payload=get(info.header_offset+offset,info.header_offset+offset+info.compress_size-1)
            data=zlib.decompress(payload,-15) if info.compress_type==8 else payload
            expected=names[info.filename]
            assert len(data)==expected['Size'] and zlib.crc32(data)==expected['Crc']
            if hits:
                (W/'selected'/info.filename).write_bytes(data)
                (W/'cafe-extra-material-acquisition032.json').write_text(json.dumps({'url':url,'bundle':expected},indent=2))
                matched.update(hits)
                with index_lock:
                    indexfile=W/'local-cab-index.json'
                    index=json.loads(indexfile.read_text('utf8'))
                    for hit in hits:index['cabs'][hit]=str(W/'selected'/info.filename)
                    indexfile.write_text(json.dumps(index,indent=2),'utf8')
                print('FOUND',pack['PackName'],info.filename,hits,flush=True)
                if matched==WANTED:found.set();return
        print('Scanned mesh/shader headers',pack['PackName'],len(infos),flush=True)

packs = json.loads((W/'catalog.json').read_text())['FullPatchPacks']
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    for result in pool.map(scan, packs): pass
if not found.is_set(): print('Some mesh/shader CABs remain unavailable')
