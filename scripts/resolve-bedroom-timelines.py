import json,UnityPy
from UnityPy.classes import PPtr
from pathlib import Path
R=Path(__file__).resolve().parents[1];W=R/'.assets';deps=json.loads((W/'bedroom-dependencies.json').read_text())
env=UnityPy.load(*[str(W/'selected'/n) for n in deps['dependencies']]);out=[]
def pointer(owner,p):return PPtr(m_FileID=p['m_FileID'],m_PathID=p['m_PathID'],assetsfile=owner.assets_file).deref()
def path(go):
    names=[go.m_Name];tr=next(c.component.read() for c in go.m_Component if c.component.type.name=='Transform')
    while tr.m_Father.m_PathID:tr=tr.m_Father.read();names.insert(0,tr.m_GameObject.read().m_Name)
    return '/'.join(names)
for obj in env.objects:
    if obj.type.name!='PlayableDirector':continue
    director=obj.read();go=director.m_GameObject.read();p=path(go)
    if not p.startswith('field_833_zone01/') or not any(n in p for n in ['Bed','Windowsofa']):continue
    if not director.m_PlayableAsset.m_PathID:continue
    root=director.m_PlayableAsset.deref();timeline=root.read_typetree();tracks=[];bindings={}
    for item in director.m_SceneBindings:
        if item.value.m_PathID:
            v=item.value.read();bindings[item.key.m_PathID]=path(v.m_GameObject.read()) if hasattr(v,'m_GameObject') else v.m_Name
    def track(o,parents):
        d=o.read_typetree();name=d.get('m_Name','');clips=[]
        for c in d.get('m_Clips',[]):
            if not c['m_Asset']['m_PathID']:continue
            a=pointer(o,c['m_Asset']);v=a.read_typetree()
            if v.get('m_Clip',{}).get('m_PathID'):
                cl=pointer(a,v['m_Clip']);clips.append({'name':cl.read().m_Name,'start':c['m_Start'],'duration':c['m_Duration'],'clipIn':c['m_ClipIn'],'speed':c['m_TimeScale'],'offset':v.get('m_Position'),'rotation':v.get('m_EulerAngles'),'asset':v})
        if clips:tracks.append({'parents':parents,'name':name,'binding':bindings.get(o.path_id),'position':d.get('m_Position'),'rotation':d.get('m_EulerAngles'),'clips':clips})
        for child in d.get('m_Children',[]):track(pointer(o,child),parents+[name])
    for t in timeline['m_Tracks']:track(pointer(root,t),[])
    out.append({'path':p,'collection':obj.assets_file.name,'pathId':obj.path_id,'timeline':timeline['m_Name'],'tracks':tracks})
(W/'bedroom-timelines.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
for row in out:
    print(row['path'],row['timeline'])
    for t in row['tracks']:print(' ',t['name'],t['binding'],[(c['name'],c['start'],c['duration'],c['offset'],c['rotation']) for c in t['clips']])
