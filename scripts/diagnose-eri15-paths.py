import UnityPy,zlib,json
from pathlib import Path
files=[p for p in Path('.assets/selected').glob('*.bundle')if'ch0304-'in p.name]
env=UnityPy.load(*map(str,files));paths={0:''};avatars={};roots=[]
def walk(go,path=''):
 paths[zlib.crc32(path.encode())]=path
 t=next(c.component.read()for c in go.m_Component if c.component.deref().type.name=='Transform')
 for p in t.m_Children:
  c=p.read().m_GameObject.read();walk(c,(path+'/'+c.m_Name).lstrip('/'))
for o in env.objects:
 if o.type.name=='Avatar':
  d=o.read_typetree()
  for k,v in d['m_TOS']:avatars[int(k)]=v
 if o.type.name=='GameObject'and o.read().m_Name=='CH0304':
  try:walk(o.read());roots.append((o.assets_file.name,o.path_id))
  except Exception as e:print(e)
rows=json.load(open('test-results/eri15-native-clip-inspection.json'))
for r in rows:
 binds=r['raw']['m_ClipBindingConstant']['genericBindings'];print(r['name'],'resolved',sum(b['path']in paths for b in binds),'/',len(binds))
 for b in binds[:10]:print(b['path'],b['attribute'],paths.get(b['path']),avatars.get(b['path']))
print('roots',roots,'paths',len(paths),'avatars',len(avatars))
Path('test-results/eri15-path-hashes.json').write_text(json.dumps(dict(paths=paths,avatars=avatars,roots=roots),indent=2),'utf8')
