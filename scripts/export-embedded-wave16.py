"""Export only audited native character/persistent roots, retaining source timing."""
from pathlib import Path
import os,sys,json,runpy
W=Path('.assets');T=Path('test-results');out=W/'cafe-embedded044';out.mkdir(exist_ok=True)
audit=json.loads((T/'wave16-embedded-initial-audit.json').read_text('utf8'))
persistent=json.loads((T/'wave16-persistent-initial-audit.json').read_text('utf8'))
profiles=json.loads((W/'furniture-profiles.json').read_text('utf8'));specs=json.loads(Path('scripts/roster-wave16.json').read_text('utf8'))
icons=sorted({r['icon']for r in audit['missing']}|{next(p['icon']for p in profiles if p['character']==r['character']and f"f{p['furnitureId']}_"in r['id'])for r in persistent['unexplained']})
os.environ['BA_FX_OUTPUT']=str(out);sys.argv=['export-cafe-effects.py',*icons];v=runpy.run_path('scripts/export-cafe-effects.py');env=v['env'];read=v['read']
for prefix,_ in specs.values():
 for p in(W/'selected').glob('character-'+prefix.lower()+'-*.bundle'):env.load_file(str(p))
def hierarchy(go):
 yield go
 t=next(read(c.component)for c in go.m_Component if c.component.deref().type.name=='Transform')
 for child in t.m_Children:yield from hierarchy(read(read(child).m_GameObject))
def score(go):
 total=0
 for g in hierarchy(go):
  for c in g.m_Component:
   if c.component.deref().type.name in ['ParticleSystemRenderer','MeshRenderer','SkinnedMeshRenderer']:total+=sum(bool(p.m_PathID)for p in read(c.component).m_Materials)
 return total
for t in v['timelines']:t['controls']=[]
effects={};rows=[]
for row in audit['missing']:
 go=next(o.read()for o in env.objects if o.type.name=='GameObject'and o.assets_file.name.lower()==row['sourceCab'].lower()and o.path_id==row['sourceId']);name=go.m_Name+'__embedded044';effects[name]=v['visit'](go)
 t=next(t for t in v['timelines']if t['icon']==row['icon'])
 for start,end in row['windows']:t['controls'].append(dict(parents=[row['group']],track='Native character-embedded FX',prefab=name,existing=True,restartOnActivation=True,bindingResolved=True,binding=go.m_Name,start=start,duration=end-start,clipIn=0,speed=1,seed=0))
 rows.append(row)
for row in persistent['unexplained']:
 c=json.loads((W/'wave16-final'/row['character']/'character.json').read_text('utf8'));f=next(f for f in c['furniture']if f['id']==row['id']);icon=f['sourceTimeline']
 roots=[o.read()for o in env.objects if o.type.name=='GameObject'and o.read().m_Name==icon and any(c.component.deref().type.name=='PlayableDirector'for c in o.read().m_Component)]
 prefab=max(roots,key=score);go=next(g for g in hierarchy(prefab)if g.m_Name==row['root']);name=icon+'__'+go.m_Name+'__persistent044';effects[name]=v['visit'](go)
 next(t for t in v['timelines']if t['icon']==icon)['controls'].append(dict(parents=[f['sourceGroup']],track='Native persistent FX',prefab=name,existing=True,bindingResolved=True,binding=go.m_Name,start=0,duration=f['duration'],clipIn=0,speed=1,seed=0))
 rows.append(row)
(out/'source.json').write_text(json.dumps(dict(timelines=v['timelines'],effects=effects,errors=v['errors'])),'utf8')
(T/'wave16-embedded-source.json').write_text(json.dumps(dict(roots=rows,errors=v['errors']),indent=2),'utf8');print('Native roots',len(rows),'errors',v['errors'])
