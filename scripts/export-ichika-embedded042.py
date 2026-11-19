"""Export Ichika's original phone UI from her character prefab, not the chair."""
from pathlib import Path
import os,sys,runpy,json
from glb import load
W=Path('.assets');out=W/'cafe-embedded042';out.mkdir(exist_ok=True)
os.environ['BA_FX_OUTPUT']=str(out);sys.argv=['export-cafe-effects.py','my_autumnsports_01_chair_03']
v=runpy.run_path('scripts/export-cafe-effects.py');env=v['env'];read=v['read']
for p in(W/'selected').glob('character-ch0071-*.bundle'):env.load_file(str(p))
def descendants(go):
 yield go
 t=next(read(c.component)for c in go.m_Component if c.component.deref().type.name=='Transform')
 for child in t.m_Children:yield from descendants(read(read(child).m_GameObject))
candidates=[]
for o in list(env.objects):
 if o.type.name!='GameObject' or o.read().m_Name!='CH0071':continue
 go=o.read();children=list(descendants(go));nonnull=0
 for child in children:
  for c in child.m_Component:
   if c.component.deref().type.name=='ParticleSystemRenderer':nonnull+=sum(bool(p.m_PathID)for p in read(c.component).m_Materials)
 candidates.append((nonnull,go,children))
score,root,children=max(candidates,key=lambda row:row[0]);assert score>0
phone=next(go for go in children if go.m_Name=='FX_my_autumnsports_01_chair_03_Phone_Emo_01')
name=phone.m_Name+'__character_existing';effect=v['visit'](phone)
d,_=load(Path('.assets/furniture-exported/all/Assets/_MX/AddressableAsset/Character/CH0071/CH0071.glb'))
metadata=next(c for c in d['scenes'][0]['extras']['BAAD_unity_animation']['clips']if c['name']=='CH0071_Cafe_my_autumnsports_01_chair_03_01')
activation=next(c for c in metadata['unity_curves']if c['attribute']=='m_IsActive'and c['path'].endswith('/'+phone.m_Name))
begin=next(k[0]for k in activation['keys']if k[1]>=.5)
timeline=v['timelines'][0];timeline['controls']=[dict(parents=['RequiredTrack_10077'],track='Original character phone UI',prefab=name,existing=True,bindingResolved=True,binding=phone.m_Name,start=begin,duration=17.3-begin,clipIn=0,speed=1,seed=0)]
source=dict(timelines=[timeline],effects={name:effect},errors=v['errors'])
(out/'source.json').write_text(json.dumps(source),'utf8')
def walk(n):
 yield n
 for c in n['children']:yield from walk(c)
rows=[dict(path=n['path'],active=n['active'],components=n['components'],materials=n.get('materials',[]),particle=n.get('particle'),animationTracks=n.get('animationTracks'))for n in walk(effect)]
Path('test-results/ichika042-embedded-source.json').write_text(json.dumps(dict(root=root.m_Name,cab=root.object_reader.assets_file.name,sourceId=phone.object_reader.path_id,rows=rows,errors=v['errors']),indent=2),'utf8')
print('Embedded phone nodes',len(rows),'errors',len(v['errors']),flush=True)
for row in rows:print(row['path'],[(m['name'],m['shader'])for m in row['materials']],flush=True)
