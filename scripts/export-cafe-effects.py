"""Export timeline-spawned original cafe effects, including their particle data.

Animation-only furniture exporters omit ControlPlayableAsset children. Keep
source timings/bindings and original geometry/textures separately for adaptation.
"""
import pathlib,json,sys,hashlib,os
import UnityPy
from UnityPy.classes import PPtr
from UnityPy.helpers.MeshHelper import MeshHandler
from source_dependencies import resolve_cached

W=pathlib.Path('.assets');dest=pathlib.Path(os.environ.get('BA_FX_OUTPUT',str(W/'cafe-fx')));dest.mkdir(exist_ok=True)
icons=sys.argv[1:] or ['my_event090_electronicgate','my_event097_racinggame','my_event081_pool','my_event14_table','my_event12_gamemachine','my_gamedevdept_01_monitor_02']
files=[p for p in (W/'selected').glob('*.bundle') if any(i.lower() in p.name.lower() for i in icons) or p.name.startswith('cafe-') and '-prefabs-' in p.name]
env=UnityPy.load(*map(str,files));effects={};timelines=[];errors=[]
def pointer(owner,p):return resolve_cached(env,lambda:PPtr(**p,assetsfile=owner.assets_file).deref())
def read(ptr):return resolve_cached(env,ptr.read)
def material(m):
    try:source_shader=read(m.m_Shader)
    except (FileNotFoundError, KeyError) as error:raise FileNotFoundError(f'{m.m_Name} shader: {error}') from error
    shader=source_shader.m_ParsedForm
    if shader.m_Name.endswith('Main_Add_Channel_Distort_1a'):
        (dest/'channel-shader.json').write_text(json.dumps(source_shader.object_reader.read_typetree()),'utf8')
    v={'name':m.m_Name,'shader':shader.m_Name,'queue':m.m_CustomRenderQueue,'floats':dict(m.m_SavedProperties.m_Floats),'colors':{k:[x.r,x.g,x.b,x.a] for k,x in m.m_SavedProperties.m_Colors},'textures':[]}
    for k,tex in m.m_SavedProperties.m_TexEnvs:
        if not tex.m_Texture.m_PathID:continue
        try:texture=read(tex.m_Texture)
        except (FileNotFoundError, KeyError) as error:
            errors.append({'material':m.m_Name,'slot':k,'reason':str(error)})
            v['textures'].append({'slot':k,'missing':str(error)});continue
        if not hasattr(texture,'image'):continue
        name=hashlib.sha256((texture.object_reader.assets_file.name+str(texture.object_reader.path_id)).encode()).hexdigest()[:16]+'.png';texture.image.save(dest/name)
        v['textures'].append({'slot':k,'file':name,'name':texture.m_Name,'srgb':bool(getattr(texture,'m_ColorSpace',0)==1),'scale':[tex.m_Scale.x,tex.m_Scale.y],'offset':[tex.m_Offset.x,tex.m_Offset.y],'wrap':[texture.m_TextureSettings.m_WrapU,texture.m_TextureSettings.m_WrapV]})
    return v
def visit(go,path=''):
    row={'name':go.m_Name,'path':path+'/'+go.m_Name,'objectId':go.object_reader.assets_file.name+':'+str(go.object_reader.path_id),'active':go.m_IsActive};parts={c.component.deref().type.name:c.component.deref() for c in go.m_Component};row['components']=list(parts);t=parts['Transform'].read()
    for key,value,axes in [('position',t.m_LocalPosition,'xyz'),('rotation',t.m_LocalRotation,'xyzw'),('scale',t.m_LocalScale,'xyz')]:row[key]=[getattr(value,k) for k in axes]
    if 'ParticleSystem' in parts:
        ps=parts['ParticleSystem'];row['particle']=ps.read_typetree();row['particleId']=ps.assets_file.name+':'+str(ps.path_id)
        sub=row['particle'].get('SubModule',{})
        if sub.get('enabled'):
            row['subEmitters']=[]
            for emitter in sub['subEmitters']:
                if not emitter['emitter']['m_PathID']:continue
                target=pointer(ps,emitter['emitter'])
                row['subEmitters'].append({'target':target.assets_file.name+':'+str(target.path_id),'type':emitter['type'],'properties':emitter['properties'],'probability':emitter['emitProbability']})
    renderer_kind='ParticleSystemRenderer' if 'ParticleSystemRenderer' in parts else 'MeshRenderer' if 'MeshRenderer' in parts and 'MeshFilter' in parts else None
    if renderer_kind:
        r=parts[renderer_kind].read();row['renderer']=parts[renderer_kind].read_typetree();row['materials']=[]
        mesh_ptr=r.m_Mesh if renderer_kind=='ParticleSystemRenderer' else parts['MeshFilter'].read().m_Mesh
        if renderer_kind=='MeshRenderer':row['staticRenderer']=True
        if mesh_ptr.m_PathID:
            try:
                mesh=read(mesh_ptr);h=MeshHandler(mesh);h.process();row['mesh']={'name':mesh.m_Name,'positions':h.m_Vertices,'uv':h.m_UV0,'uv2':h.m_UV1,'colors':h.m_Colors,'triangles':h.get_triangles()}
                if h.m_Normals:row['mesh']['normals']=h.m_Normals
            except (FileNotFoundError, KeyError) as error:
                row.setdefault('missing',[]).append(str(error));errors.append({'effect':row['path'],'reason':str(error),'meshPointer':str(mesh_ptr)})
        for ptr in r.m_Materials:
            if not ptr.m_PathID:continue
            try:row['materials'].append(material(read(ptr)))
            except (FileNotFoundError, KeyError) as error:row.setdefault('missing',[]).append(str(error));errors.append({'effect':row['path'],'reason':str(error),'materialPointer':str(ptr),'owner':ptr.assetsfile.name,'external':str(ptr.assetsfile.externals[ptr.m_FileID-1].path) if ptr.m_FileID else None})
    if 'PlayableDirector' in parts:
        director=parts['PlayableDirector'].read();bindings={}
        for pair in director.m_SceneBindings:
            if not pair.value.m_PathID:continue
            component=read(pair.value);target=read(component.m_GameObject) if hasattr(component,'m_GameObject') else component
            bindings[str(pair.key.m_PathID)]=target.m_Name
        tracks=[]
        def animation_track(o,inherited=None):
            data=o.read_typetree();binding=bindings.get(str(o.path_id),inherited)
            if data.get('m_InfiniteClip',{}).get('m_PathID'):
                tracks.append({'binding':binding,'start':0,'clipIn':0,'speed':1,'clip':pointer(o,data['m_InfiniteClip']).read_typetree()})
            for segment in data.get('m_Clips',[]):
                if not segment.get('m_Asset',{}).get('m_PathID'):continue
                asset=pointer(o,segment['m_Asset']);a=asset.read_typetree()
                if a.get('m_Clip',{}).get('m_PathID'):
                    tracks.append({'binding':binding,'start':segment['m_Start'],'duration':segment['m_Duration'],'clipIn':segment['m_ClipIn'],'speed':segment['m_TimeScale'],'clip':pointer(asset,a['m_Clip']).read_typetree()})
            for child in data.get('m_Children',[]):animation_track(pointer(o,child),binding)
        if director.m_PlayableAsset.m_PathID:
            timeline=read(director.m_PlayableAsset)
            for child in timeline.object_reader.read_typetree().get('m_Tracks',[]):animation_track(pointer(timeline.object_reader,child))
        row['animationTracks']=tracks
    row['children']=[visit(read(read(c).m_GameObject),row['path']) for c in t.m_Children];return row
def track(o,parents,binding):
    d=o.read_typetree();name=d.get('m_Name','');result=[]
    # Character groups are authored muted and enabled by the game's selected student.
    for c in d.get('m_Clips',[]):
        if not c.get('m_Asset',{}).get('m_PathID'):continue
        a=pointer(o,c['m_Asset']);v=a.read_typetree()
        exposed=v.get('sourceGameObject',{}).get('exposedName')
        source_go=binding.get(str(exposed))
        default=v.get('sourceGameObject',{}).get('defaultValue',{})
        if source_go is None and default.get('m_PathID'):
            source_go=pointer(a,default).read()
        existing=not v.get('prefabGameObject',{}).get('m_PathID')
        if existing:
            go=source_go
            if go is None:continue
        else:go=pointer(a,v['prefabGameObject']).read()
        n=go.m_Name
        if existing:n+='__existing'
        if n not in effects:
            try:effects[n]=visit(go)
            except (FileNotFoundError, KeyError) as error:errors.append({'effect':n,'reason':str(error)})
        result.append({'parents':parents,'track':name,'prefab':n,'existing':existing,'bindingResolved':source_go is not None,'exposedReference':exposed,'binding':source_go.m_Name if source_go is not None else name,'start':c['m_Start'],'duration':c['m_Duration'],'clipIn':c['m_ClipIn'],'speed':c['m_TimeScale'],'seed':v.get('particleRandomSeed',0)})
    for p in d.get('m_Children',[]):result.extend(track(pointer(o,p),parents+[name],binding))
    return result
def director_priority(o):
    # Timeline bundles also contain stripped same-name director stubs. Prefer
    # the instantiated furniture prefab, which retains exposed bone bindings.
    if o.type.name!='PlayableDirector':return -1
    return sum(bool(p['m_PathID']) for _,p in o.read_typetree().get('m_ExposedReferences',{}).get('m_References',[]))

for o in sorted(list(env.objects),key=director_priority,reverse=True):
    if o.type.name!='PlayableDirector':continue
    dr=o.read();icon=dr.m_GameObject.read().m_Name
    if icon not in icons or not dr.m_PlayableAsset.m_PathID:continue
    if any(r['icon']==icon for r in timelines):continue
    binding={}
    for key,p in o.read_typetree().get('m_ExposedReferences',{}).get('m_References',[]):
        if p['m_PathID']:
            v=pointer(o,p).read();binding[str(key)]=v if hasattr(v,'m_Component') else read(v.m_GameObject)
    root=resolve_cached(env,dr.m_PlayableAsset.deref);controls=[]
    for p in root.read_typetree()['m_Tracks']:controls.extend(track(pointer(root,p),[],binding))
    if icon=='my_event088_retractwindow':
        # This background runs directly on the furniture prefab; it is not a
        # ControlPlayable spawn. Its transform already exists in the base GLB.
        def background(go):
            if go.m_Name=='FX_my_event088_retractwindow_BG':return go
            t=next(read(c.component) for c in go.m_Component if c.component.deref().type.name=='Transform')
            for child in t.m_Children:
                result=background(read(read(child).m_GameObject))
                if result:return result
        bg=background(read(dr.m_GameObject))
        if bg:
            name=bg.m_Name+'__existing';effects[name]=visit(bg)
            profiles=json.loads((W/'furniture-profiles.json').read_text('utf8'))
            duration=max(c['start']+c['duration'] for p in profiles if p['icon']==icon and p['group']=='RequiredTrack_10134' for c in p['studentTrack']['clips'])
            controls.append({'parents':['RequiredTrack_10134'],'track':'Authored background','prefab':name,'existing':True,'binding':bg.m_Name,'start':0,'duration':duration,'clipIn':0,'speed':1,'seed':0})
    timelines.append({'icon':icon,'directorCab':o.assets_file.name,'controls':controls});print(icon,len(controls),flush=True)
(dest/'source.json').write_text(json.dumps({'timelines':timelines,'effects':effects,'errors':errors},indent=2),'utf8')
print('Effects',len(effects),'unresolved',len(errors),flush=True)
