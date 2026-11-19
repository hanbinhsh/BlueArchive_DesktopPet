"""Read-only comparison of active persistent particles and installed scenes."""
from pathlib import Path
import json,UnityPy
from glb import load

profiles=json.loads(Path('.assets/furniture-profiles.json').read_text('utf8'))
icons={p['icon']for p in profiles}
files=[p for p in Path('.assets/selected').glob('*.bundle')if '-prefabs-'in p.name and (p.name.startswith('cafe-') or any(icon.lower()in p.name.lower()for icon in icons))]
env=UnityPy.load(*map(str,files));prefabs={}
for obj in list(env.objects):
 if obj.type.name!='GameObject':continue
 go=obj.read()
 if go.m_Name in icons and any(c.component.deref().type.name=='PlayableDirector'for c in go.m_Component):prefabs[go.m_Name]=go
def roots(go,active=True,particle_parent=False):
 parts={c.component.deref().type.name:c.component.deref()for c in go.m_Component}
 active=active and bool(go.m_IsActive)
 if not active:return
 if 'ParticleSystem'in parts and not particle_parent:
  yield go.m_Name
 for child in parts['Transform'].read().m_Children:yield from roots(child.read().m_GameObject.read(),active,particle_parent or 'ParticleSystem'in parts)
report=[]
for cp in Path('characters').glob('*/character.json'):
 for f in json.loads(cp.read_text('utf8')).get('furniture',[]):
  d,b=load(cp.parent/f['model']);metadata=d['scenes'][0].get('extras',{}).get('BA_furniture',{})
  icon=f.get('sourceTimeline',metadata.get('sourceTimeline'))
  if icon not in prefabs:continue
  original=list(roots(prefabs[icon]))
  if not original:continue
  rendered={name for m in d['materials']for name in m.get('extras',{}).get('BA_cafeParticle',{}).get('sourceName','').split('/')}
  report.append(dict(character=cp.parent.name,id=f['id'],icon=icon,activePersistentRoots=original,notParticleAdapted=[name for name in original if name not in rendered]))
activation=json.loads(Path('test-results/activation035-source.json').read_text('utf8'))
unexplained=[]
for row in report:
 row['idleOnlyExclusions']=[]
 for name in row['notParticleAdapted']:
  tracks=[t for t in activation if t['icon']==row['icon']and t.get('binding')==name and t['path'][0]=='Object_Idle']
  if tracks:row['idleOnlyExclusions'].append(dict(root=name,group='Object_Idle',muted=all(bool(t['muted'])for t in tracks)))
  else:unexplained.append(dict(character=row['character'],id=row['id'],root=name))
Path('test-results/persistent037-audit.json').write_text(json.dumps(dict(prefabsScanned=len(prefabs),rows=report,unexplained=unexplained),indent=2),'utf8')
print('Scanned',len(prefabs),'prefabs; persistent scenes',len(report),'candidates',[(r['character'],r['id'],r['notParticleAdapted'])for r in report if r['notParticleAdapted']])
candidates=[]
for icon in {r['icon']for r in report if r['notParticleAdapted']}:
 wanted={n for r in report if r['icon']==icon for n in r['notParticleAdapted']}
 def particles(go):
  parts={c.component.deref().type.name:c.component.deref()for c in go.m_Component}
  if 'ParticleSystem'in parts:
   p=parts['ParticleSystem'].read_typetree();r=parts.get('ParticleSystemRenderer')
   yield dict(name=go.m_Name,active=bool(go.m_IsActive),rendererEnabled=bool(r.read().m_Enabled)if r else None,playOnAwake=p.get('playOnAwake'),loop=p.get('looping'),emission=p.get('EmissionModule',{}).get('enabled'))
  for child in parts['Transform'].read().m_Children:yield from particles(child.read().m_GameObject.read())
 def scan(go):
  if go.m_Name in wanted:candidates.append(dict(icon=icon,root=go.m_Name,particles=list(particles(go))))
  tr=next(c.component.read()for c in go.m_Component if c.component.deref().type.name=='Transform')
  for child in tr.m_Children:scan(child.read().m_GameObject.read())
 scan(prefabs[icon])
Path('test-results/persistent037-candidates.json').write_text(json.dumps(candidates,indent=2),'utf8')
for row in candidates:print(row)
