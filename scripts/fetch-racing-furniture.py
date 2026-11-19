"""Acquire only the r97 racing furniture members, using verified ZIP ranges."""
import concurrent.futures, io, json, pathlib, struct, zipfile, zlib, sys
import httpx

ROOT=pathlib.Path(__file__).resolve().parents[1]
WORK=ROOT/'.assets/r97'
BASE='https://prod-clientpatch.bluearchiveyostar.com/r97_s71wespocqarqo4ywey2/Windows_PatchPack/'
shared_fx='--shared-fx' in sys.argv
if shared_fx and '--r97' not in sys.argv:
    WORK=ROOT/'.assets'
    BASE='https://prod-clientpatch.bluearchiveyostar.com/r96_nvji95owgkbcxlmkb8mi/Windows_PatchPack/'
catalog=json.loads((WORK/'catalog.json').read_text('utf8'))
def selected(name):
    if shared_fx:return 'effectsfreezed' in name and ('material' in name or 'texture' in name)
    return 'my_event097_racinggame-' in name or name.startswith('cafe-_mxload-prefabs-2026-09-30_')

def acquire(pack):
    wanted={b['Name']:b for b in pack['BundleFiles'] if selected(b['Name'])}
    if not wanted:return []
    with httpx.Client(timeout=120,follow_redirects=True) as client:
        def fetch(start,end):
            r=client.get(BASE+pack['PackName'],headers={'Range':f'bytes={start}-{end}'})
            r.raise_for_status()
            if r.status_code!=206 or len(r.content)!=end-start+1:raise RuntimeError('Invalid byte range response')
            return r.content
        size=pack['PackSize'];start=max(0,size-262144)
        tail=fetch(start,size-1)
        end=tail.rfind(b'PK\x05\x06')
        if end<0:raise RuntimeError('Missing ZIP end record')
        central_size,central_offset=struct.unpack_from('<II',tail,end+12)
        stream=io.BytesIO();stream.seek(start);stream.write(tail)
        if central_offset<start:
            stream.seek(central_offset);stream.write(fetch(central_offset,central_offset+central_size-1))
        with zipfile.ZipFile(stream) as archive:infos=[i for i in archive.infolist() if i.filename in wanted]
        assert len(infos)==len(wanted)
        result=[]
        for info in infos:
            expected=wanted[info.filename];target=WORK/'selected'/info.filename
            raw=target.read_bytes() if target.exists() else b''
            if len(raw)!=expected['Size'] or zlib.crc32(raw)!=expected['Crc']:
                header=fetch(info.header_offset,info.header_offset+29)
                name_len,extra_len=struct.unpack_from('<HH',header,26)
                offset=info.header_offset+30+name_len+extra_len
                payload=fetch(offset,offset+info.compress_size-1)
                raw=zlib.decompress(payload,-15) if info.compress_type==8 else payload
                assert len(raw)==expected['Size'] and zlib.crc32(raw)==expected['Crc']
                target.write_bytes(raw)
            result.append({'url':BASE+pack['PackName'],'bundle':expected})
        print(pack['PackName'],len(result),flush=True)
        return result

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    result=[r for group in pool.map(acquire,catalog['FullPatchPacks']) for r in group]
(WORK/('shared-fx-acquisition.json' if shared_fx else 'racing-furniture-acquisition.json')).write_text(json.dumps(result,indent=2),'utf8')
