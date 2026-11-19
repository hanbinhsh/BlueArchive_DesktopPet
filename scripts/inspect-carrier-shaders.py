"""Inspect original carrier particle shader bytecode using Windows D3DDisassemble."""
import pathlib,json,ctypes,UnityPy,lz4.block,os,struct
from UnityPy.export.ShaderConverter import ShaderProgram
from UnityPy.streams import EndianBinaryReader
from source_dependencies import resolve_cached
out=pathlib.Path('.assets/carrier-shaders');out.mkdir(exist_ok=True)
source=json.loads(pathlib.Path(os.environ.get('BA_FX_SOURCE','.assets/cafe-fx')+'/source.json').read_text('utf8'));icons=[t['icon'] for t in source['timelines']]
env=UnityPy.load(*map(str,[p for p in pathlib.Path('.assets/selected').glob('*.bundle') if any(i in p.name for i in icons)]))
dll=ctypes.WinDLL('d3dcompiler_47.dll');dis=dll.D3DDisassemble;dis.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_uint,ctypes.c_char_p,ctypes.POINTER(ctypes.c_void_p)];dis.restype=ctypes.c_long
wanted=set()
def collect(n):
 for m in n.get('materials',[]):wanted.add(m['shader'].rsplit('/',1)[-1])
 for c in n['children']:collect(c)
for n in source['effects'].values():collect(n)
seen=set();objects=list(env.objects)
for o in list(objects):
 if o.type.name=='ParticleSystemRenderer':
  for ptr in o.read().m_Materials:
   if ptr.m_PathID:
    try:objects.append(resolve_cached(env,ptr.deref))
    except (KeyError,FileNotFoundError):pass
for o in objects:
 if o.type.name!='Material':continue
 mat=o.read()

 try:shader=resolve_cached(env,mat.m_Shader.read)
 except (KeyError,FileNotFoundError):continue
 name=shader.m_ParsedForm.m_Name.rsplit('/',1)[-1]
 if name in seen or name not in wanted:continue
 seen.add(name);d=shader.object_reader.read_typetree();(out/(name+'.json')).write_text(json.dumps(d['m_ParsedForm'],indent=2),'utf8')
 one=lambda a:a[0][0] if isinstance(a[0],list) else a[0]
 off=one(shader.offsets);n=one(shader.compressedLengths);size=one(shader.decompressedLengths)
 raw=lz4.block.decompress(bytes(shader.compressedBlob)[off:off+n],uncompressed_size=size)
 codes=[];offset=0
 while True:
  offset=raw.find(b'DXBC',offset)
  if offset<0:break
  size=struct.unpack_from('<I',raw,offset+24)[0]
  if 32<=size<=len(raw)-offset:codes.append(raw[offset:offset+size])
  offset+=4
 for i,code in enumerate(codes):
  blob=ctypes.c_void_p();hr=dis(code,len(code),0,None,ctypes.byref(blob))
  # Parameter blobs also occupy this table and may contain incidental DXBC
  # bytes. Only successfully decoded programs are retained as evidence.
  if hr:continue
  table=ctypes.cast(blob,ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
  get=ctypes.WINFUNCTYPE(ctypes.c_void_p,ctypes.c_void_p)(table[3]);length=ctypes.WINFUNCTYPE(ctypes.c_size_t,ctypes.c_void_p)(table[4]);release=ctypes.WINFUNCTYPE(ctypes.c_ulong,ctypes.c_void_p)(table[2])
  text=ctypes.string_at(get(blob),length(blob)).rstrip(b'\0').decode();release(blob)
  (out/(name+f'-{i}.txt')).write_text(text,'utf8')
 print(name,len(codes))
