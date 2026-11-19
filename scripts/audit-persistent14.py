"""Check every active native particle root of the five new furniture scenes."""
from pathlib import Path
import json,UnityPy
from glb import load
W=Path('.assets');ids=set(json.loads(Path('scripts/roster-wave14.json').read_text('utf8')))
profiles=[p for p in json.loads((W/'furniture-profiles.json').read_text('utf8'))if p['character']in ids];icons={p['icon']for p in profiles}
env=UnityPy.load(*map(str,[p for p in (W/'selected').glob('*.bundle')if '-prefabs-'in p.name and(p.name.startswith('cafe-')or any(i.lower()in p.name.lower()for i in icons))]));prefabs={}
for o in list(env.objects):
 if o.type.name!='GameObject':continue
 go=o.read()
 if go.m_Name in icons and any(c.component.deref().type.name=='PlayableDirector'for c in go.m_Component):prefabs[go.m_Name]=go
def roots(go,active=True,parent_ps=False):
 parts={c.component.deref().type.name:c.component.deref()for c in go.m_Component};active=active and bool(go.m_IsActive)
 if not active:return
 if'ParticleSystem'in parts and not parent_ps:yield go.m_Name
 for ch in parts['Transform'].read().m_Children:yield from roots(ch.read().m_GameObject.read(),active,parent_ps or'ParticleSystem'in parts)
rows=[]
for key in ids:
 folder=W/'wave14-final'/key;c=json.loads((folder/'character.json').read_text('utf8'))
 for f in c.get('furniture',[]):
  d,_=load(folder/f['model']);icon=f['sourceTimeline'];native=list(roots(prefabs[icon]));rendered={n for m in d['materials']for n in m.get('extras',{}).get('BA_cafeParticle',{}).get('sourceName','').split('/')}
  rows.append({'character':key,'id':f['id'],'icon':icon,'activePersistentRoots':native,'notParticleAdapted':[n for n in native if n not in rendered]})
activation=json.loads(Path('test-results/activation035-source.json').read_text('utf8'))
for row in rows:
 row['idleOnlyExclusions']=[n for n in row['notParticleAdapted']if any(t['icon']==row['icon']and t['binding']==n and t['path'][0]=='Object_Idle'for t in activation)]
result={'prefabsScanned':len(prefabs),'rows':rows,'unexplained':[{'character':r['character'],'id':r['id'],'root':n}for r in rows for n in r['notParticleAdapted']if n not in r['idleOnlyExclusions']]}
Path('test-results/wave14-persistent-audit.json').write_text(json.dumps(result,indent=2),'utf8');print(json.dumps(result,indent=2))
