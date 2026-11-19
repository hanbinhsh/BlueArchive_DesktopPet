"""Probe remote bundle directories, downloading a full bundle only on CAB match."""
import concurrent.futures, importlib.util, json, pathlib, struct, sys, threading, zlib
import httpx
ROOT = pathlib.Path(__file__).resolve().parents[1]; W = ROOT/'.assets'
spec = importlib.util.spec_from_file_location('cab',ROOT/'scripts/find-cab.py')
cab = importlib.util.module_from_spec(spec); spec.loader.exec_module(cab)
wanted = sys.argv[1].lower(); found = threading.Event()
BASE = 'https://prod-clientpatch.bluearchiveyostar.com/r96_nvji95owgkbcxlmkb8mi/Windows_PatchPack/'
def scan(pack):
    if found.is_set() or (W/'packs'/pack['PackName']).exists(): return
    candidates = {b['Name']:b for b in pack['BundleFiles'] if ('-shaders-' in b['Name'] if '--shaders' in sys.argv else '-textures-' in b['Name'] or ('--materials' in sys.argv and '-materials-' in b['Name']))}
    if not candidates: return
    with httpx.Client(timeout=60,follow_redirects=True,transport=httpx.HTTPTransport(retries=3)) as client:
        url = BASE+pack['PackName']; size = pack['PackSize']
        def get(start,end):
            end = min(end,size-1)
            r = client.get(url,headers={'Range':f'bytes={start}-{end}'})
            r.raise_for_status()
            assert r.status_code == 206 and len(r.content) == end-start+1
            return r.content
        tail = get(max(0,size-131072),size-1); offset = tail.find(b'PK\x01\x02')
        checked = 0
        while offset >= 0 and tail[offset:offset+4] == b'PK\x01\x02':
            method = struct.unpack_from('<H',tail,offset+10)[0]
            compressed = struct.unpack_from('<I',tail,offset+20)[0]
            nl,el,cl = struct.unpack_from('<HHH',tail,offset+28)
            start = struct.unpack_from('<I',tail,offset+42)[0]
            name = tail[offset+46:offset+46+nl].decode(); offset += 46+nl+el+cl
            if name not in candidates: continue
            if found.is_set(): return
            raw = get(start,start+30+nl+min(compressed,16384)+255)
            n,e = struct.unpack_from('<HH',raw,26); data_start = 30+n+e
            def decode(data): return zlib.decompressobj(-15).decompress(data) if method == 8 else data
            prefix = decode(raw[data_start:data_start+compressed])
            try: names = cab.cab_names(prefix)
            except ValueError:
                raw = get(start+data_start,start+data_start+compressed-1)
                prefix = decode(raw); names = cab.cab_names(prefix)
            checked += 1
            if wanted not in names: continue
            payload = get(start+data_start,start+data_start+compressed-1)
            data = decode(payload); expected = candidates[name]
            assert len(data) == expected['Size'] and zlib.crc32(data) == expected['Crc']
            (W/'selected'/name).write_bytes(data)
            evidence = W/'wave5-extra-dependencies.json'; records = json.loads(evidence.read_text())
            records.append({'pack':pack['PackName'],'url':url,'bundle':expected})
            evidence.write_text(json.dumps(records,indent=2))
            found.set(); print('FOUND',name,flush=True); return
        print('Probed',pack['PackName'],checked,flush=True)
packs = json.loads((W/'catalog.json').read_text())['FullPatchPacks']
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    errors = []
    for future in concurrent.futures.as_completed([pool.submit(scan,p) for p in packs]):
        try: future.result()
        except Exception as error: errors.append(str(error))
if not found.is_set(): raise RuntimeError('CAB not found in remote texture bundles: '+str(errors))
