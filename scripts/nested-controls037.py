"""Restore nested ice-pool ControlPlayable timing from its original director."""
from pathlib import Path
import json,sys,UnityPy
from UnityPy.classes import PPtr
from source_dependencies import resolve_cached
from glb import load,save
env=UnityPy.load(*map(str,Path('.assets/selected').glob('*event062*prefabs*.bundle')))
def read(p):return resolve_cached(env,p.read)
def ptr(o,p):return resolve_cached(env,lambda:PPtr(**p,assetsfile=o.assets_file).deref())
controls=[]
for o in list(env.objects):
 if o.type.name!='PlayableDirector':continue
 dr=o.read()
 if dr.m_GameObject.read().m_Name!='FX_my_event062_icepool_01':continue
 refs={str(k):ptr(o,p).read().m_Name for k,p in o.read_typetree()['m_ExposedReferences']['m_References'] if p['m_PathID']}
 def walk(track):
  d=track.read_typetree()
  for clip in d.get('m_Clips',[]):
   asset=ptr(track,clip['m_Asset']).read_typetree()
   if not asset.get('updateParticle'):continue
   controls.append({'target':refs[str(asset['sourceGameObject']['exposedName'])],'start':clip['m_Start'],'duration':clip['m_Duration'],'clipIn':clip['m_ClipIn'],'speed':clip['m_TimeScale']})
  for child in d.get('m_Children',[]):walk(ptr(track,child))
 timeline=resolve_cached(env,dr.m_PlayableAsset.deref)
 for track in timeline.read_typetree()['m_Tracks']:walk(ptr(timeline,track))
 break
assert controls
p=Path(sys.argv[1])/'eimi_swimsuit/f210327_0.glb';d,b=load(p);count=0
for m in d['materials']:
 s=m.get('extras',{}).get('BA_cafeParticle')
 if not s or 'FX_my_event062_icepool_01/' not in s['sourceName']:continue
 matches=[c for c in controls if c['target'] in s['sourceName'].split('/')]
 if not matches:continue
 c=max(matches,key=lambda c:s['sourceName'].split('/').index(c['target']))
 s['propertyClock']=dict(s['control']);s['control']={**s['control'],**{k:c[k]for k in ['start','duration','clipIn','speed']}};s['persistent']=False;count+=1
save(p,d,b)
Path('test-results/nested037-controls.json').write_text(json.dumps({'controls':controls,'particles':count},indent=2),'utf8');print('Restored nested clocks',count)
