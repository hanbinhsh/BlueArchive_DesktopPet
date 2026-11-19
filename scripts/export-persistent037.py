"""Append omitted active prefab effects; exclude idle-only timeline objects."""
import os,sys,runpy,json
from pathlib import Path
os.environ['BA_FX_OUTPUT']='.assets/cafe-persistent037'
audit=json.loads(Path('test-results/persistent037-audit.json').read_text('utf8'))['rows']
icons=['my_cafe_01_b_table_01','my_poolparty_01_b_sofa_01','my_gamecenter_01_p_dollcrane','my_gamecenter_01_p_hockey','my_event076_board']
sys.argv=['export-cafe-effects.py',*icons]
v=runpy.run_path('scripts/export-cafe-effects.py');env=v['env'];read=v['read'];report=[]
profiles=json.loads(Path('.assets/furniture-profiles.json').read_text('utf8'))
def roots(go,active=True,parent_ps=False):
 parts={c.component.deref().type.name:c.component.deref()for c in go.m_Component}
 active=active and bool(go.m_IsActive)
 if not active:return
 if 'ParticleSystem'in parts and not parent_ps:yield go
 for child in parts['Transform'].read().m_Children:yield from roots(read(read(child).m_GameObject),active,parent_ps or 'ParticleSystem'in parts)
for timeline in v['timelines']:
 timeline['controls']=[];icon=timeline['icon']
 wanted={name for row in audit if row['icon']==icon for name in row['notParticleAdapted']}
 go=next(o.read()for o in list(env.objects)if o.type.name=='GameObject'and o.read().m_Name==icon and any(c.component.deref().type.name=='PlayableDirector'for c in o.read().m_Component))
 for root in roots(go):
  if root.m_Name not in wanted:continue
  key=root.m_Name+'__existing';v['effects'][key]=v['visit'](root)
  for profile in [p for p in profiles if p['icon']==icon]:
   duration=max(c['start']+c['duration']for c in profile['studentTrack']['clips'])
   timeline['controls'].append(dict(parents=[profile['group']],track='Original persistent FX',prefab=key,existing=True,bindingResolved=True,binding=root.m_Name,start=0,duration=duration,clipIn=0,speed=1,seed=0))
  report.append(dict(icon=icon,root=root.m_Name))
Path('.assets/cafe-persistent037/source.json').write_text(json.dumps(dict(timelines=v['timelines'],effects=v['effects'],errors=v['errors'])),'utf8')
Path('test-results/persistent037-source.json').write_text(json.dumps(report,indent=2),'utf8');print('Added roots',len(report),'errors',len(v['errors']))
