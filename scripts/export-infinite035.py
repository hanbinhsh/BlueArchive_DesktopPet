import pathlib,json,UnityPy,sys
sys.path.insert(0,'scripts');from source_dependencies import resolve_cached
from UnityPy.classes import PPtr
files=[p for p in pathlib.Path('.assets/selected').glob('*.bundle') if '-timelines-' in p.name or p.name.startswith('cafe-') and '-prefabs-' in p.name]
env=UnityPy.load(*map(str,files));out=[];seen=set();activities=[]
def ptr(o,p):return resolve_cached(env,lambda:PPtr(**p,assetsfile=o.assets_file).deref())
for o in sorted(list(env.objects),key=lambda o:len(o.read().m_SceneBindings) if o.type.name=='PlayableDirector' else -1,reverse=True):
 if o.type.name!='PlayableDirector':continue
 dr=o.read();icon=dr.m_GameObject.read().m_Name
 if icon in seen or not dr.m_PlayableAsset.m_PathID:continue
 seen.add(icon)
 bindings={}
 for b in dr.m_SceneBindings:
  if b.value.m_PathID:
   obj=resolve_cached(env,b.value.read)
   if hasattr(obj,'m_GameObject'):bindings[str(b.key.m_PathID)]=resolve_cached(env,obj.m_GameObject.read).m_Name
   elif hasattr(obj,'m_Component'):bindings[str(b.key.m_PathID)]=obj.m_Name
 root=resolve_cached(env,dr.m_PlayableAsset.deref)
 def tr(o,parents):
  d=o.read_typetree();path=parents+[d.get('m_Name','')]
  if d.get('m_Clips'):
   for segment in d['m_Clips']:
    if not segment.get('m_Asset',{}).get('m_PathID'):continue
    asset=ptr(o,segment['m_Asset']);values=asset.read_typetree()
    script=ptr(asset,values['m_Script']).read().m_ClassName if values.get('m_Script',{}).get('m_PathID') else ''
    if script=='ActivationPlayableAsset':activities.append({'icon':icon,'path':path,'binding':bindings.get(str(o.path_id)),'start':segment['m_Start'],'duration':segment['m_Duration'],'muted':d.get('m_Muted',0)})
  if d.get('m_InfiniteClip',{}).get('m_PathID'):
   cl=ptr(o,d['m_InfiniteClip']);out.append({'icon':icon,'path':path,'track':d,'clip':cl.read_typetree()})
  for p in d.get('m_Children',[]):tr(ptr(o,p),path)
 for p in root.read_typetree().get('m_Tracks',[]):tr(ptr(root,p),[])
pathlib.Path('test-results/infinite035-source.json').write_text(json.dumps(out),'utf8');pathlib.Path('test-results/activation035-source.json').write_text(json.dumps(activities,indent=2),'utf8');print('override tracks',len(out),'activation segments',len(activities))
