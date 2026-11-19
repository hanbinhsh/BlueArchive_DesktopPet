import UnityPy
from pathlib import Path
import sys
sys.path.insert(0,'scripts');from source_dependencies import resolve_cached
files=[p for p in Path('.assets/selected').glob('*.bundle') if 'lemontree' in p.name or p.name.startswith('cafe-') and '-prefabs-' in p.name];env=UnityPy.load(*map(str,files));read=lambda p:resolve_cached(env,p.read)
def w(go,depth=0):
 parts=[read(c.component) for c in go.m_Component];types=[c.object_reader.type.name for c in parts]
 if True:print(' '*depth,go.m_Name,types)
 for c in parts:
  if c.object_reader.type.name=='Transform':
   for ch in c.m_Children:w(read(read(ch).m_GameObject),depth+1)
for o in list(env.objects):
 if o.type.name=='PlayableDirector':
  dr=o.read();go=read(dr.m_GameObject)
  if go.m_Name=='my_event058_lemontree':w(go)


