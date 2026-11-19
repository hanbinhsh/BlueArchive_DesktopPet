"""Append original animations to adapted rigs without rebuilding their materials.

Every missing track has an explicit reason; unknown renderer bindings are never
silently ignored. Existing actions, corrected curves and furniture remain intact.
"""
import copy, json, pathlib, re, sys, shutil, traceback, os
import UnityPy
from glb import load, save, append_view, compact
from visibility import attach_visibility
from mouth_events import mouth_events
from renderer_event_layout import renderer_event_layout
R=pathlib.Path(__file__).resolve().parents[1];W=R/'.assets'
index=json.loads((R/'test-results/action-source-index.json').read_text(encoding='utf8'))
output=W/'expanded-ready';output.mkdir(exist_ok=True)
requested=sys.argv[1:] or list(index)
profiles=json.loads(pathlib.Path(os.environ['BA_ACTION_PROFILES']).read_text(encoding='utf8')) if os.environ.get('BA_ACTION_PROFILES') else {}
source_dirs=[pathlib.Path(p) for p in json.loads(os.environ.get('BA_SOURCE_DIRS','[]'))] or [W/p for p in ['selected','costume-audit','costume-variants']]
files={p.name:p for folder in source_dirs for p in folder.glob('*.bundle')}
env=UnityPy.load(*map(str,files.values()))
roots={}
for obj in env.objects:
    if obj.type.name!='GameObject':continue
    go=obj.read()
    if go.m_Name not in {v[0]['root'] for v in index.values() if v}:continue
    transform=next((c.component.read() for c in go.m_Component if c.component.deref().type.name=='Transform'),None)
    if transform and not transform.m_Father.m_PathID:roots[go.m_Name]=go
def renderer_names(go):
    result=[]
    for c in go.m_Component:
        value=c.component.read();kind=value.object_reader.type.name
        if kind in ('SkinnedMeshRenderer','MeshRenderer'):result.append(go.m_Name)
        if kind=='Transform':
            for child in value.m_Children:result.extend(renderer_names(child.read().m_GameObject.read()))
    return result
corrections={'junko_newyear':{9:'CH0192_Body_Face01_Outline',10:'CH0192_Body_Face_Outline'},
             'reisa':{5:'CH0167_Body_Face01_Outline',6:'CH0167_Body_Face_Outline'},
             'koyuki':{3:'CH0198_Face01_Outline',4:'CH0198_Face_Outline'},
             'koyuki_pajamas':{4:'CH0310_Face01_Mesh',5:'CH0310_Face02_Mesh'},
             'shun_swimsuit_small':{3:'CH0355_02_Face01_Mesh',4:'CH0355_02_Face02_Mesh'}}
def describe(name,root):
    suffix=name.removeprefix(root+'_')
    for marker in ['Cafe_','Formation_','Victory_','Normal_','Kneel_','Stand_','Move_','Vital_','Exs','Public','Rearrange_','TSS_']:
        if marker in suffix:suffix=suffix[suffix.index(marker):];break
    lower=suffix.lower()
    category='技能' if re.search('exs|public|skill',lower) else '编队与胜利' if re.search('formation|victory|rearrange',lower) else '移动' if re.search('move|walk|run',lower) else '剧情' if re.search('cafe|interaction|field|scenario',lower) else '战斗'
    words={'Cafe':'咖啡厅','Formation':'编队','Victory':'胜利','Normal':'常规','Kneel':'蹲姿','Stand':'掩体站姿','Move':'移动','Vital':'状态','Exs':'EX 技能','Public':'普通技能','Rearrange':'重新编队','Idle':'待机','Pickup':'提起','Reaction':'互动','Attack':'攻击','Reload':'换弹','Callsign':'回应','Start':'开始','End':'结束','Ing':'持续','ing':'持续','Delay':'间隔','Jump':'跳跃','Death':'倒下','Dying':'濒危','Panic':'惊慌','Retreat':'撤退','Walk':'走路','Run':'跑步'}
    label=' · '.join(words.get(w,w) for w in suffix.split('_'))
    return suffix,category,label
report_path=R/'test-results/action-expansion.json'
reports=[r for r in json.loads(report_path.read_text(encoding='utf8')) if r['character'] not in requested] if report_path.exists() else []
for key in requested:
    staged=R/os.environ.get('BA_ACTION_BASE','.assets/wave8-ready')/key
    source_dir=staged if (staged/'character.json').exists() else R/'characters'/key
    target=output/key;shutil.copytree(source_dir,target,dirs_exist_ok=True)
    manifest=json.loads((source_dir/'character.json').read_text(encoding='utf8'))
    doc,binary=load(source_dir/'model.glb');extras=doc['scenes'][0].setdefault('extras',{})
    row={'character':key,'before':len(manifest['actions']),'added':[],'unavailable':[]}
    if not index[key]:
        row['unavailable'].append({'reason':'No matching complete source export'});reports.append(row);continue
    source=index[key][0];raw,data=load(R/source['path']);row['source']=source['path']
    same_layout=len(raw['nodes'])==len(doc['nodes']) and all(a.get('name')==b.get('name') and a.get('children')==b.get('children') for a,b in zip(raw['nodes'],doc['nodes']))
    metadata={c['track']:c for c in raw['scenes'][0].get('extras',{}).get('BAAD_unity_animation',{}).get('clips',[])}
    names={}
    for i,n in enumerate(doc['nodes']):names.setdefault(n.get('name',''),[]).append(i)
    layout=renderer_names(roots[source['root']]) if source['root'] in roots else []
    layout=renderer_event_layout(key,layout)
    for i,name in corrections.get(key,{}).items():
        while len(layout)<=i:layout.append('')
        layout[i]=name
    used={a['clip'] for a in manifest['actions']}
    acc_map={};view_map={}
    def accessor(old):
        if old in acc_map:return acc_map[old]
        acc=copy.deepcopy(raw['accessors'][old]);assert 'sparse' not in acc
        v=acc['bufferView']
        if v not in view_map:
            view=raw['bufferViews'][v];start=view.get('byteOffset',0)
            view_map[v]=append_view(doc,binary,data[start:start+view['byteLength']],view.get('target'))
            if 'byteStride' in view:doc['bufferViews'][view_map[v]]['byteStride']=view['byteStride']
        acc['bufferView']=view_map[v];acc_map[old]=len(doc['accessors']);doc['accessors'].append(acc);return acc_map[old]
    for animation in raw.get('animations',[]):
        if animation['name'] in used:continue
        clip=metadata.get(animation['name']);reason=None
        if not clip:reason='Missing original event metadata'
        elif re.search(r'Cafe_Interact|Cafe_Prop|TSS_Interact',clip['name'],re.I):reason='Requires matching furniture or companion scene; use furniture interactions'
        channels=[]
        for channel in animation['channels']:
            c=copy.deepcopy(channel);node=c['target'].get('node')
            if node is None:reason='Non-node animation target';break
            n=raw['nodes'][node].get('name','');matches=names.get(n,[])
            if same_layout:matches=[node]
            elif len(matches)>1:
                matches=[i for i in matches if ('mesh' in raw['nodes'][node])==('mesh' in doc['nodes'][i]) and ('skin' in raw['nodes'][node])==('skin' in doc['nodes'][i])]
            if len(matches)!=1:reason='Missing or ambiguous rig node: '+n;break
            c['target']['node']=matches[0];channels.append(c)
        if not reason:
            trial={'nodes':doc['nodes'],'scenes':[{'extras':{'BAAD_unity_animation':{'clips':[clip]}}}]}
            # The current original Izuna prefab has four renderers. These old
            # index-4 events address a removed fifth renderer; retain the source
            # event and explicitly record its absence, as for the common clips.
            ignored=[{'clip':clip['name'],'index':e['int'],'function':e['function'],'time':e['time']} for e in clip['events'] if key=='izuna' and len(layout)==4 and e['int']==4 and e['function'] in ('AniEvt_EnableChildRenderer','AniEvt_DisableChildRenderer')]
            ignored += [e for e in profiles.get(key,{}).get('ignoredRendererEvents',[]) if e['clip']==clip['name']]
            try:attach_visibility(trial,layout,ignored_events=ignored)
            except (IndexError,ValueError) as error:reason='Unresolved renderer event: '+str(error)
        if reason:
            row['unavailable'].append({'clip':clip['name'] if clip else animation['name'],'reason':reason});continue
        result=copy.deepcopy(animation);result['channels']=channels
        for sampler in result['samplers']:
            for field in ['input','output']:sampler[field]=accessor(sampler[field])
        doc['animations'].append(result)
        extras['BAAD_unity_animation']['clips'].append(copy.deepcopy(clip))
        extras.setdefault('BA_pet_visibility',{'defaults':{},'clips':{}})['clips'][clip['track']]=trial['scenes'][0]['extras']['BA_pet_visibility']['clips'][clip['track']]
        if ignored:doc.setdefault('extras',{}).setdefault('BA_unresolved_legacy_renderer_events',[]).extend(ignored)
        suffix,category,label=describe(clip['name'],source['root'])
        action_id='original_'+re.sub('[^a-z0-9]+','_',suffix.lower()).strip('_')
        if any(a['id']==action_id for a in manifest['actions']):action_id+='_'+str(len(manifest['actions']))
        manifest['actions'].append({'id':action_id,'label':label,'clip':clip['track'],'sourceName':clip['name'],'category':category})
        if manifest.get('mouth'):manifest['mouth']['events'][clip['track']]=mouth_events(clip,manifest['mouth']['defaultTile'])
        row['added'].append({'id':action_id,'clip':clip['name'],'channels':len(channels)})
    for a in manifest['actions']:a.setdefault('category','常用')
    binary=compact(doc,binary);save(target/'model.glb',doc,binary)
    (target/'character.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
    row['after']=len(manifest['actions']);reports.append(row)
    (R/'test-results/action-expansion.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')
    print(key,row['before'],'->',row['after'],'excluded',len(row['unavailable']),flush=True)
(R/'test-results/action-expansion.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')
