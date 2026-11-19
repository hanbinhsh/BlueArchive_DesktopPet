"""Keep authored timeline segments and Animator bindings for cafe interactions."""
import json,pathlib,re,os
import UnityPy
from UnityPy.classes import PPtr
from source_dependencies import resolve_cached
R=pathlib.Path(__file__).resolve().parents[1];W=R/'.assets'
idx=json.loads((W/'furniture-index.json').read_text(encoding='utf8'))
partner_specs=json.loads((R/'scripts/furniture-partners.json').read_text(encoding='utf8'))
students=json.loads((W/os.environ.get('BA_STUDENTS_SNAPSHOT','students-audit-2026-10-21.json')).read_text(encoding='utf8'))
deps=json.loads((W/'furniture-dependencies.json').read_text())
names=[n for n in deps if 'timelines' in n or 'animationclips' in n or '-prefabs-' in n]
env=UnityPy.load(*[str(W/'selected'/n) for n in names]);out=[]
def pointer(owner,p):
    return resolve_cached(env,lambda:PPtr(m_FileID=p['m_FileID'],m_PathID=p['m_PathID'],assetsfile=owner.assets_file).deref())
for obj in list(env.objects):
    if obj.type.name!='PlayableDirector':continue
    director=obj.read();icon=director.m_GameObject.read().m_Name
    matched=[x for x in idx['entries'] if x['icon'].lower()==icon.lower()]
    if not matched:continue
    for entry in matched:entry['icon']=icon
    if not director.m_PlayableAsset.m_PathID:continue
    root=director.m_PlayableAsset.deref();timeline=root.read_typetree();tracks=[];bindings={}
    for binding in director.m_SceneBindings:
        key,val=binding.key,binding.value
        if not val.m_PathID:continue
        component=val.read()
        if hasattr(component,'m_GameObject'):bindings[key.m_PathID]=component.m_GameObject.read().m_Name
    def track(o,parents):
        d=o.read_typetree();name=d.get('m_Name','');clips=[]
        for c in d.get('m_Clips',[]):
            if not c['m_Asset']['m_PathID']:continue
            a=pointer(o,c['m_Asset']);v=a.read_typetree()
            if v.get('m_Clip',{}).get('m_PathID'):
                cl=pointer(a,v['m_Clip'])
                clips.append({'name':cl.read().m_Name,'start':c['m_Start'],'duration':c['m_Duration'],'clipIn':c['m_ClipIn'],'speed':c['m_TimeScale'],'offset':v.get('m_Position'),'rotation':v.get('m_EulerAngles')})
        if clips:tracks.append({'parents':parents,'name':name,'binding':bindings.get(o.path_id),'position':d.get('m_Position'),'rotation':d.get('m_EulerAngles'),'clips':clips})
        for p in d.get('m_Children',[]):track(pointer(o,p),parents+[name])
    try:
        for p in timeline['m_Tracks']:track(pointer(root,p),[])
        out.append({'icon':icon,'tracks':tracks})
    except Exception as ex:out.append({'icon':icon,'error':str(ex),'tracks':tracks})
(W/'furniture-timelines.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
print('Resolved',len(out),'errors',[(v['icon'],v['error']) for v in out if 'error' in v],flush=True)
profiles={};bindings={}
specs={}
for p in (R/'scripts').glob('roster-*.json'):
    specs.update(json.loads(p.read_text(encoding='utf8')))
specs.update({'junko':['Zunko_Original',''],'junko_newyear':['CH0192',''],'serika_swimsuit':['CH0189',''],'serika':['Serika_Original',''],'serika_newyear':['Serika_Newyear','']})
specs.update(partner_specs)
primary_entries=list(idx['entries'])
for student in students.values():
    if student['PathName'] not in partner_specs:continue
    for entry in primary_entries:
        timeline=next((t for t in out if t['icon']==entry['icon']),None)
        if timeline and any(re.fullmatch(str(student['Id'])+r'(?:_\d+)?',tr['name']) for tr in timeline['tracks']):
            idx['entries'].append({**entry,'character':student['PathName'],'studentId':student['Id'],'devName':student['DevName']})
for entry in idx['entries']:
    t=next((t for t in out if t['icon']==entry['icon']),None)
    if not t:continue
    student=str(10098 if entry['character']=='hoshino_battle' else entry['studentId'])
    student_tracks=[v for v in t['tracks'] if re.fullmatch(student+r'(?:_\d+)?',v['name']) and v['parents'] and not v['parents'][0].startswith('BgmTrack')]
    for st in student_tracks:
        group=st['parents'][0]
        # Multi-seat activation groups are kept in the audit until the complete
        # participant/activation hierarchy has been verified.
        key=f"{entry['character']}:{entry['furnitureId']}:{group}:{st['name']}"
        ft=[v for v in t['tracks'] if v is not st and v['parents'] and v['parents'][0]==group and v['binding']]
        if '_' in st['name']:
            branch=st['name'].rsplit('_',1)[1]
            ft=[v for v in ft if not re.search(r'_\d+$',v['name']) or v['name'].endswith('_'+branch)]
        if not ft:ft=[v for v in t['tracks'] if v['parents']==['Object_Idle'] and v['binding']]
        rootname={'toki':'CH0187_CafeOnly','hoshino_battle':'CH0258_01','otogi':'CH0174_CafeOnly','wakamo':'Cafe_Wakamo_Original'}.get(entry['character'],specs[entry['character']][0])
        profiles[key]={**entry,'group':group,'studentTrack':st,'furnitureTracks':ft,'root':rootname,'participants':re.findall(r'\d{5}',group)}
        if entry['character']=='otogi':
            profiles[key]['bodyModel']='.assets/otogi-cafe-adapted/otogi/model.glb'
        bindings.setdefault(rootname,set()).update(c['name'] for c in st['clips'])
        for tr in ft:bindings.setdefault(tr['binding'],set()).update(c['name'] for c in tr['clips'])
(W/'furniture-profiles.json').write_text(json.dumps(list(profiles.values()),indent=2,ensure_ascii=False),encoding='utf8')
(W/'furniture-bindings.json').write_text(json.dumps({k:sorted(v) for k,v in bindings.items()},indent=2))
print('Profiles',len(profiles),'roots',len(bindings),flush=True)

