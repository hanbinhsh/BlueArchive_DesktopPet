"""Preserve the mini-game's original nested activation/control windows."""
import os,sys,runpy,json
from pathlib import Path
os.environ['BA_FX_OUTPUT']='.assets/cafe-blocks037'
sys.argv=['export-cafe-effects.py','my_event088_gamingspace']
v=runpy.run_path('scripts/export-cafe-effects.py');env=v['env'];read=v['read'];ptr=v['pointer'];report=[]
for name,effect in v['effects'].items():
 if 'Block_Extra' not in name:continue
 go=next(o.read()for o in list(env.objects)if o.type.name=='GameObject' and o.read().m_Name==name)
 director=next(c.component.deref()for c in go.m_Component if c.component.deref().type.name=='PlayableDirector')
 dr=director.read();refs={str(k):ptr(director,p).read()for k,p in director.read_typetree()['m_ExposedReferences']['m_References']if p['m_PathID']}
 bindings={str(pair.key.m_PathID):read(pair.value)for pair in dr.m_SceneBindings if pair.value.m_PathID}
 def path(target):
  if hasattr(target,'m_GameObject'):target=read(target.m_GameObject)
  names=[]
  for _ in range(32):
   names.append(target.m_Name)
   if target.object_reader.path_id==go.object_reader.path_id:return '/'+ '/'.join(reversed(names))
   tr=next(read(c.component)for c in target.m_Component if c.component.deref().type.name=='Transform')
   if not tr.m_Father.m_PathID:break
   target=read(read(tr.m_Father).m_GameObject)
  raise ValueError('Nested binding is outside effect: '+str(names))
 nodes={}
 def register(n):
  assert n['objectId']not in nodes,n['objectId'];nodes[n['objectId']]=n
  for c in n['children']:register(c)
 register(effect)
 def track(o):
  data=o.read_typetree()
  for clip in data.get('m_Clips',[]):
   a=ptr(o,clip['m_Asset']).read_typetree();target=None
   if 'sourceGameObject'in a:
    target=refs.get(str(a['sourceGameObject']['exposedName']))
   elif len(a)<=5:target=bindings.get(str(o.path_id))
   if target is None:continue
   if hasattr(target,'m_GameObject'):target=read(target.m_GameObject)
   key=target.object_reader.assets_file.name+':'+str(target.object_reader.path_id);n=nodes[key]
   window={'start':clip['m_Start'],'duration':clip['m_Duration'],'clipIn':clip['m_ClipIn'],'speed':clip['m_TimeScale'],'kind':'control' if 'sourceGameObject'in a else 'activation'}
   n.setdefault('activationWindows',[]).append(window);report.append({'effect':name,'path':path(target),'objectId':key,**window})
  for child in data.get('m_Children',[]):track(ptr(o,child))
 timeline=read(dr.m_PlayableAsset)
 for t in timeline.object_reader.read_typetree()['m_Tracks']:track(ptr(timeline.object_reader,t))
Path('.assets/cafe-blocks037/source.json').write_text(json.dumps({'timelines':v['timelines'],'effects':v['effects'],'errors':v['errors']}),'utf8')
Path('test-results/blocks037-windows.json').write_text(json.dumps(report,indent=2),'utf8');print('Nested windows',len(report))
