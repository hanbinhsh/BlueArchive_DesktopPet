"""Export always-running furniture effects omitted by Timeline-only traversal."""
import os,sys,runpy,json
from pathlib import Path
os.environ['BA_FX_OUTPUT']='.assets/cafe-static037'
sys.argv=['export-cafe-effects.py','my_gehennaparty_01_table_02','my_event065_chairmandesk']
v=runpy.run_path('scripts/export-cafe-effects.py');env=v['env'];read=v['read']
profiles=json.loads(Path('.assets/furniture-profiles.json').read_text('utf8'))
def roots(go,particle_parent=False):
    parts={c.component.deref().type.name:c.component.deref()for c in go.m_Component}
    if 'ParticleSystem' in parts and not particle_parent:yield go
    for c in parts['Transform'].read().m_Children:
        yield from roots(read(read(c).m_GameObject),particle_parent or 'ParticleSystem' in parts)
for timeline in v['timelines']:
    icon=timeline['icon'];candidates=[o.read() for o in list(env.objects)if o.type.name=='GameObject' and o.read().m_Name==icon]
    go=next(g for g in candidates if any(c.component.deref().type.name=='PlayableDirector' for c in g.m_Component))
    for root in roots(go):
        print('ROOT',icon,root.m_Name,flush=True)
        key=root.m_Name+'__existing';v['effects'][key]=v['visit'](root)
        for profile in [p for p in profiles if p['icon']==icon]:
            duration=max(c['start']+c['duration']for c in profile['studentTrack']['clips'])
            timeline['controls'].append({'parents':[profile['group']],'track':'Original persistent FX','prefab':key,'existing':True,'bindingResolved':True,'binding':root.m_Name,'start':0,'duration':duration,'clipIn':0,'speed':1,'seed':0})
Path('.assets/cafe-static037/source.json').write_text(json.dumps({'timelines':v['timelines'],'effects':v['effects'],'errors':v['errors']}),'utf8')
