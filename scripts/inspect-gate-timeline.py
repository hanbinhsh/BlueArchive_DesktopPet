import pathlib,UnityPy,json
from UnityPy.classes import PPtr
files=[p for p in pathlib.Path('.assets/selected').glob('*.bundle') if any(x in p.name for x in ['2984646745','my_event090_electronicgate','ch0307'])]
e=UnityPy.load(*map(str,files));out=[]
def pointer(o,p):return PPtr(**p,assetsfile=o.assets_file).deref()
def track(o):
 d=o.read_typetree();row={'data':d,'clips':[],'children':[]}
 for c in d.get('m_Clips',[]):
  if c.get('m_Asset',{}).get('m_PathID'):row['clips'].append(pointer(o,c['m_Asset']).read_typetree())
 for p in d.get('m_Children',[]):row['children'].append(track(pointer(o,p)))
 return row
for o in list(e.objects):
 if o.type.name=='PlayableDirector' and o.read().m_GameObject.read().m_Name=='my_event090_electronicgate':
  dr=o.read();root=dr.m_PlayableAsset.deref();out.append({'director':o.read_typetree(),'tracks':[track(pointer(root,p)) for p in root.read_typetree()['m_Tracks']]})
pathlib.Path('test-results/gate-timeline-full.json').write_text(json.dumps(out,indent=2),'utf8');print(len(out))
