"""Restore native character-bound and persistent furniture FX from audited roots."""
from pathlib import Path
import json,os,sys,runpy
W=Path('.assets');T=Path('test-results');dest=W/'cafe-embedded043';dest.mkdir(exist_ok=True)
audit=json.loads((T/'wave15-embedded-initial-audit.json').read_text('utf8'))
persistent=json.loads((T/'wave15-persistent-initial-audit.json').read_text('utf8'))
icons=sorted({r['icon']for r in audit['missing']})
os.environ['BA_FX_OUTPUT']=str(dest);sys.argv=['export-cafe-effects.py',*icons]
v=runpy.run_path('scripts/export-cafe-effects.py');env=v['env'];read=v['read']
for p in(W/'selected').glob('character-ch0267-*.bundle'):env.load_file(str(p))
profiles=json.loads((W/'furniture-profiles.json').read_text('utf8'))
for t in v['timelines']:t['controls']=[]
effects={};records=[]
def go_from(cab,ident):
 return next(o.read()for o in env.objects if o.type.name=='GameObject'and o.assets_file.name.lower()==cab.lower()and o.path_id==ident)
for row in audit['missing']:
 go=go_from(row['sourceCab'],row['sourceId']);name=go.m_Name+'__embedded043';effects[name]=v['visit'](go)
 t=next(t for t in v['timelines']if t['icon']==row['icon'])
 for start,end in row['windows']:
  t['controls'].append(dict(parents=[row['group']],track='Native character-embedded FX',prefab=name,existing=True,restartOnActivation=True,bindingResolved=True,binding=go.m_Name,start=start,duration=end-start,clipIn=0,speed=1,seed=0))
 records.append(row)
for row in persistent['unexplained']:
 p=next(p for p in profiles if p['character']==row['character']and p['furnitureId']==13204)
 roots=[o.read()for o in env.objects if o.type.name=='GameObject'and o.read().m_Name==row['root']]
 # Prefer a root with actual particle descendants/materials over stripped stubs.
 def score(go):
  parts={c.component.deref().type.name:c.component for c in go.m_Component}
  return sum(bool(p.m_PathID)for p in read(parts['ParticleSystemRenderer']).m_Materials)if'ParticleSystemRenderer'in parts else 0
 go=max(roots,key=score);name=go.m_Name+'__persistent043';effects[name]=v['visit'](go)
 c=json.loads((W/'wave15-final'/row['character']/'character.json').read_text('utf8'));f=next(f for f in c['furniture']if f['id']==row['id'])
 next(t for t in v['timelines']if t['icon']==p['icon'])['controls'].append(dict(parents=[p['group']],track='Native persistent fountain',prefab=name,existing=True,bindingResolved=True,binding=go.m_Name,start=0,duration=f['duration'],clipIn=0,speed=1,seed=0))
 records.append(row)
source=dict(timelines=v['timelines'],effects=effects,errors=v['errors'])
(dest/'source.json').write_text(json.dumps(source),'utf8');(T/'wave15-embedded-source.json').write_text(json.dumps(dict(roots=records,errors=v['errors']),indent=2),'utf8')
print('Native roots',len(records),'errors',len(v['errors']))
