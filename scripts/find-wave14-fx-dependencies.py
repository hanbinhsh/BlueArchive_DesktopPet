"""Locate referenced CABs using only remote ZIP/UnityFS directory headers.

Only matching bundles are downloaded in full and CRC checked. This deliberately
does not fetch the game's whole texture library.
"""
import pathlib,json,struct,zlib,threading,concurrent.futures,time,re
import httpx,lz4.block
W=pathlib.Path('.assets');BASE='https://prod-clientpatch.bluearchiveyostar.com/r96_nvji95owgkbcxlmkb8mi/Windows_PatchPack/'
wanted={m[0] for e in json.loads((W/'cafe-wave14/source.json').read_text())['errors'] if (m:=re.findall(r'cab-[a-f0-9]+',e['reason']))}
cachefile=W/'remote-cab-headers.json';cache=json.loads(cachefile.read_text()) if cachefile.exists() else {};found=set();lock=threading.Lock();acquired=[]
local=json.loads((W/'local-cab-index.json').read_text());known={pathlib.Path(p).name for p in local['files']};found.update(wanted&set(local['cabs']))
def cabs(data):
 if not data.startswith(b'UnityFS\0'):return []
 o=8;version=struct.unpack_from('>I',data,o)[0];o+=4
 for _ in range(2):o=data.index(b'\0',o)+1
 size,compressed,uncompressed,flags=struct.unpack_from('>QIII',data,o);o+=20
 if version>=7:o=(o+15)//16*16
 if flags&128:raise ValueError('Directory at end')
 if len(data)<o+compressed:raise EOFError()
 raw=data[o:o+compressed]
 if flags&63 in [2,3]:raw=lz4.block.decompress(raw,uncompressed_size=uncompressed)
 elif flags&63:raise ValueError('Unsupported directory compression')
 return sorted(set(x.decode().lower() for x in re.findall(rb'CAB-[a-fA-F0-9]{32}|cab-[a-fA-F0-9]{32}',raw)))
def scan(pack):
 names={b['Name']:b for b in pack['BundleFiles'] if ('material' in b['Name'] or 'texture' in b['Name']) and b['Name'] not in known and (b['Name'] not in cache or bool(set(cache[b['Name']])&wanted-found))}
 if not names:return
 with lock:
  if found>=wanted:return
 with httpx.Client(timeout=45,follow_redirects=True) as client:
  def get(start,end):
   for attempt in range(3):
    try:
     r=client.get(BASE+pack['PackName'],headers={'Range':f'bytes={start}-{end}'});r.raise_for_status()
     if r.status_code!=206 or len(r.content)!=end-start+1:raise ValueError('Invalid range')
     return r.content
    except httpx.HTTPError:
     if attempt==2:raise
     time.sleep(attempt+1)
  size=pack['PackSize'];start=max(0,size-65536);tail=get(start,size-1);end=tail.rfind(b'PK\x05\x06')
  length,offset=struct.unpack_from('<II',tail,end+12);directory=tail[offset-start:offset-start+length] if offset>=start else get(offset,offset+length-1)
  entries=[];p=0
  while p<len(directory):
   assert directory[p:p+4]==b'PK\x01\x02'
   method=struct.unpack_from('<H',directory,p+10)[0];compressed=struct.unpack_from('<I',directory,p+20)[0];nl,xl,cl=struct.unpack_from('<HHH',directory,p+28);header=struct.unpack_from('<I',directory,p+42)[0];name=directory[p+46:p+46+nl].decode();p+=46+nl+xl+cl
   if name in names:entries.append((name,method,compressed,header))
  for name,method,compressed,header in entries:
   with lock:
    if found>=wanted:return
   ids=cache.get(name)
   raw=None;data_offset=None
   if ids is None or bool(set(ids)&wanted-found):
    header_bytes=get(header,header+29);nl,xl=struct.unpack_from('<HH',header_bytes,26);data_offset=header+30+nl+xl
   if ids is None:
    ids=[]
    for cap in [4096,16384,65536]:
     raw=get(data_offset,data_offset+min(cap,compressed)-1)
     data=zlib.decompressobj(-15).decompress(raw) if method==8 else raw
     try:ids=cabs(data);break
     except (EOFError,struct.error,ValueError):
      if cap==65536:print('HEADER_UNREADABLE',name,flush=True)
    with lock:cache[name]=ids
   hits=set(ids)&wanted-found
   if hits:
    raw=get(data_offset,data_offset+compressed-1);data=zlib.decompress(raw,-15) if method==8 else raw
    expected=names[name];assert len(data)==expected['Size'] and zlib.crc32(data)==expected['Crc']
    (W/'selected'/name).write_bytes(data)
    with lock:found.update(hits);acquired.append({'bundle':name,'url':BASE+pack['PackName'],'cabs':sorted(hits),'bytes':len(data)});print('FOUND',name,sorted(hits),flush=True)
  with lock:cachefile.write_text(json.dumps(cache,indent=2));print('Scanned',pack['PackName'],len(entries),'found',len(found),'/',len(wanted),flush=True)
packs=json.loads((W/'catalog.json').read_text())['FullPatchPacks']
packs.sort(key=lambda p:0 if 'Prologue' in p['PackName'] else 1 if any('effectsfreezed' in b['Name'] for b in p['BundleFiles']) else 2)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for result in pool.map(scan,packs):pass
(W/'wave14-fx-dependencies.json').write_text(json.dumps({'acquired':acquired,'missing':sorted(wanted-found)},indent=2));print('Missing',wanted-found)
