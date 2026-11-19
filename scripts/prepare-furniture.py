"""Compose original cafe timelines with the already verified student geometry.

No procedural student animation is introduced. Unity timeline segments are
sampled at 30 Hz, including clip-in, speed, gaps, mouth and renderer events.
"""
import copy,io,json,pathlib,re,sys,math,os
import numpy as np
import UnityPy
from glb import load,save,read_accessor,append_accessor,append_view,compact
from mouth_events import mouth_events
from visibility import attach_visibility
from timeline_visibility import boolean_curves
from furniture_geometry import restore_geometry
from furniture_fx import adapt_masked_fx
from furniture_water_fx import adapt_water_fx
from furniture_tint import adapt_simple_tint
from prop_materials import adapt_prop_material
from prop_visibility import apply_prop_visibility
from renderer_event_layout import renderer_event_layout
R=pathlib.Path(__file__).resolve().parents[1];W=R/'.assets'
character_root=pathlib.Path(os.environ.get('BA_CHARACTER_OUTPUT',R/'characters'))
append_only=os.environ.get('BA_FURNITURE_APPEND')=='1'
view_yaws=json.loads((R/'scripts/furniture-view-yaw.json').read_text())
character_view_yaws=json.loads((R/'scripts/furniture-character-view-yaw.json').read_text())
profiles=json.loads((W/'furniture-profiles.json').read_text(encoding='utf8'))
all_profiles=profiles
if os.environ.get('BA_FURNITURE_PROFILES'):profiles=json.loads(pathlib.Path(os.environ['BA_FURNITURE_PROFILES']).read_text(encoding='utf8'))
profiles=[p for p in profiles if (character_root/p['character']/'character.json').exists()]
requested=sys.argv[1:]
if requested:profiles=[p for p in profiles if p['character'] in requested]
export=W/'furniture-exported/all'
source_files=[str(p) for p in (W/'selected').glob('*.bundle')]
builtins=W/'jp/windows/.state/runtime/1.73.459696/Package/Extracted/assets/bin/Data/unity default resources'
if builtins.exists():source_files.append(str(builtins))
env=UnityPy.load(*source_files)
gameobjects={}
for obj in list(env.objects):
    if obj.type.name=='GameObject':
        go=obj.read();gameobjects.setdefault(go.m_Name,[]).append(go)

def prefab(name):
    candidates=gameobjects[name]
    directors=[go for go in candidates if any(c.component.deref().type.name=='PlayableDirector' for c in go.m_Component)]
    if directors:
        # Dependency bundles contain same-name stripped prefab stubs. The
        # instantiated cafe root retains actual mesh/material references.
        def score(go):
            renderable=sum(bool(getattr(r,'m_Mesh',None)and r.m_Mesh.m_PathID) for _,r,_ in renderers(go))
            concrete=pathlib.Path(go.object_reader.assets_file.parent.name).name.lower().startswith('cafe-')
            return renderable,concrete
        return max(directors,key=score)
    return next((go for go in candidates if '_mxload-prefabs-' in pathlib.Path(go.object_reader.assets_file.parent.name).name.lower()),candidates[0])
def character_directory(pack):
    public=character_root/pack
    if not (public/'character.json').exists():public=R/'characters'/pack
    return public if (public/'character.json').exists() else W/'furniture-partners'/pack
def renderers(go):
    found=[]
    def visit(go,active=True):
        active=active and bool(go.m_IsActive)
        for cp in go.m_Component:
            obj=cp.component.deref()
            if obj.type.name in ('SkinnedMeshRenderer','MeshRenderer'):
                v=obj.read();found.append((go.m_Name,v,active and bool(v.m_Enabled)))
            elif obj.type.name=='Transform':
                for child in obj.read().m_Children:visit(child.read().m_GameObject.read(),active)
    visit(go);return found
def exported(name):
    files=[p for p in export.rglob(name+'*.glb') if p.stat().st_size>=20 and re.fullmatch(re.escape(name)+r'(?:_\d+)?',p.stem)]
    if not files:raise ValueError('Export missing: '+name)
    return load(max(files,key=lambda p:p.stat().st_mtime))

def adapt_furniture(doc,data,icon):
    originals={n:r for n,r,_ in renderers(prefab(icon))};defaults={n:v for n,_,v in renderers(prefab(icon))}
    restore_geometry(doc,data,originals,defaults)
    # Removed null source renderers leave orphan export meshes. Prune those
    # before replacing material indices; compact() retains all mesh primitives.
    used=sorted({n['mesh'] for n in doc['nodes'] if 'mesh' in n});remap={old:new for new,old in enumerate(used)}
    doc['meshes']=[doc['meshes'][i] for i in used]
    for node in doc['nodes']:
        if 'mesh' in node:node['mesh']=remap[node['mesh']]
    mats={m.read().m_Name:m.read() for r in originals.values() for m in r.m_Materials if m.m_PathID}
    rebuilt=[];indices={};seen_meshes=set()
    for node in doc['nodes']:
        if 'mesh' not in node:continue
        if node['mesh'] in seen_meshes:continue
        seen_meshes.add(node['mesh'])
        original_name=node.get('name','')
        if original_name not in originals:original_name=re.sub(r'_\d+$','',original_name)
        renderer=originals.get(original_name)
        if renderer is not None and renderer.m_Materials and not any(m.m_PathID for m in renderer.m_Materials):
            node.pop('mesh',None);node.pop('skin',None);defaults[original_name]=False;continue
        primitives=doc['meshes'][node['mesh']]['primitives']
        for i,primitive in enumerate(primitives):
            name=doc['materials'][primitive['material']]['name']
            renderer=originals.get(original_name)
            # Prefabs may override the shared mesh's material (chairs/glass).
            # The original renderer's ordered slots are authoritative.
            if renderer is not None and len(renderer.m_Materials)==len(primitives):
                name=renderer.m_Materials[i].read().m_Name
            elif name=='DefaultMaterial':
                raise ValueError('Unresolved merged furniture renderer '+node['name'])
            if name not in indices:indices[name]=len(rebuilt);rebuilt.append({'name':name})
            primitive['material']=indices[name]
    doc['materials']=rebuilt
    texcache={}
    for mat in doc['materials']:
        original=mats.get(mat['name'])
        if original is None:raise ValueError('Unresolved furniture material '+mat['name'])
        textures=dict(original.m_SavedProperties.m_TexEnvs)
        tex=textures.get('_MainTex')
        if tex and tex.m_Texture.m_PathID:
            texture=tex.m_Texture.read();key=(texture.object_reader.assets_file.name,texture.object_reader.path_id)
            if key not in texcache:
                png=io.BytesIO();texture.image.save(png,format='PNG')
                image=len(doc.setdefault('images',[]));doc['images'].append({'bufferView':append_view(doc,data,png.getvalue()),'mimeType':'image/png'})
                texcache[key]=len(doc.setdefault('textures',[]));doc['textures'].append({'source':image})
            mat['pbrMetallicRoughness']={'baseColorTexture':{'index':texcache[key]},'metallicFactor':0,'roughnessFactor':1}
        elif 'baseColorTexture' not in mat.get('pbrMetallicRoughness',{}):
            color=dict(original.m_SavedProperties.m_Colors).get('_Color')
            if color is None:raise ValueError('Furniture material has no verified texture or color '+mat['name'])
            mat['pbrMetallicRoughness']={'baseColorFactor':[max(0,min(1,v)) for v in [color.r,color.g,color.b,color.a]],'metallicFactor':0,'roughnessFactor':1}
        mat['extensions']={'KHR_materials_unlit':{}}
        floats=dict(original.m_SavedProperties.m_Floats)
        mat['doubleSided']=floats.get('_Cull',2)==0
        # Opaque Unity materials commonly store unrelated data in texture alpha.
        # Treating every cafe texture as a cutout erases whole desks and chairs.
        blended = original.m_CustomRenderQueue>=3000 or (floats.get('_SrcBlend') in (1,5) and floats.get('_DstBlend')==10)
        mat['alphaMode']='MASK' if floats.get('_AlphaClip',0) or floats.get('_AlphaClipEnable',0) or '_ENV_CUTOUT_MODE' in original.m_ValidKeywords else 'BLEND' if blended else 'OPAQUE'
        if blended:
            color=dict(original.m_SavedProperties.m_Colors).get('_Color')
            if color:mat['pbrMetallicRoughness'].setdefault('baseColorFactor',[1,1,1,1])[3]=max(0,min(1,color.a))
        if original.m_Name=='my_event090_electronicgate_glass':
            tint=dict(original.m_SavedProperties.m_Colors)['_Tint']
            mat['pbrMetallicRoughness']['baseColorFactor']=[tint.r,tint.g,tint.b,tint.a]
            mat['alphaMode']='BLEND';mat['extras']={'BA_depthWrite':False,'BA_sourceColorProperty':'_Tint'}
        # Verified original FX/Stencil/Mask Simple shader: Blend Zero One,
        # ZWrite Off. Its white _Color property is unused by the actual shader.
        # Keep this helper invisible; do not convert it to a white solid wall.
        shader=original.m_Shader
        external=original.object_reader.assets_file.externals[shader.m_FileID-1].path.lower() if shader.m_FileID else ''
        if shader.m_PathID==-1388563276506995367 and 'cab-38d7f184c16228480d78cd7ea10cae27' in external:
            # MX/Water uses _BaseColor; _Color is a leftover grey material value.
            # Approximate its refractive surface with the authored water tint/alpha.
            color=dict(original.m_SavedProperties.m_Colors)['_BaseColor']
            mat['pbrMetallicRoughness']['baseColorFactor']=[color.r,color.g,color.b,color.a]
            mat['alphaMode']='BLEND'
            mat['extras']={'BA_waterSurface':True,'BA_sourceShader':'MX/Water','BA_sourceColorProperty':'_BaseColor'}
        if shader.m_PathID==-1189838917732900529:
            # Use the original water surface color, not the almost-transparent
            # shallow-depth color. Full screen-depth refraction is not in GLB.
            color=dict(original.m_SavedProperties.m_Colors)['_SurfaceColor']
            mat['pbrMetallicRoughness']['baseColorFactor']=[color.r,color.g,color.b,color.a]
            mat['alphaMode']='BLEND';mat['extras']={'BA_waterSurface':True}
        if shader.m_PathID==-8245771139842610876 and 'cab-428091522b4007f213bf16532c4528a1' in external:
            mat['extras']={'BA_nonVisual':True,'BA_sourceShader':'FX/Stencil/Mask Simple','BA_stencil':{'mode':'mask','ref':int(floats['_StencilIndex']),'order':original.m_CustomRenderQueue-2000}}
            mat['pbrMetallicRoughness']['baseColorFactor']=[1,1,1,0];mat['alphaMode']='BLEND'
        if shader.m_PathID==4108838956398087977 and 'cab-38d7f184c16228480d78cd7ea10cae27' in external:
            mat['extras']={'BA_sourceShader':'MX/E-CafeStencil','BA_stencil':{'mode':'not-equal','ref':int(floats['_StencilIndex']),'order':original.m_CustomRenderQueue-2000}}
        if mat['alphaMode']=='MASK':mat['alphaCutoff']=floats.get('_Cutoff',.5)
        adapt_masked_fx(original,mat,doc,data)
        adapt_water_fx(original,mat,doc,data)
        adapt_simple_tint(original,mat)
        adapt_prop_material(mat)
        if original.m_Name=='FX_my_event062_icepool_01':
            # Original MX/E-Standard water layer explicitly disables ZWrite.
            # Preserve it when rebuilding, not only in the installed GLB.
            assert floats['_ZWrite']==0
            mat.setdefault('extras',{})['BA_depthWrite']=False
    for mesh in doc.get('meshes',[]):
        for p in mesh['primitives']:p['attributes'].pop('COLOR_0',None)
    return defaults

def merge(doc,data,other,raw,namespace='furniture'):
    offsets={k:len(doc.setdefault(k,[])) for k in ['bufferViews','accessors','images','textures','samplers','materials','meshes','skins','nodes']}
    data.extend(b'\0'*(-len(data)%4));start=len(data);data.extend(raw)
    other=copy.deepcopy(other)
    for v in other.get('bufferViews',[]):v['byteOffset']=v.get('byteOffset',0)+start
    for a in other.get('accessors',[]):a['bufferView']+=offsets['bufferViews']
    for i in other.get('images',[]):i['bufferView']+=offsets['bufferViews']
    for t in other.get('textures',[]):
        t['source']+=offsets['images']
        if 'sampler' in t:t['sampler']+=offsets['samplers']
    for m in other.get('materials',[]):
        def remap_textures(value):
            if not isinstance(value,dict):return
            for k,v in value.items():
                if k.endswith('Texture') and isinstance(v,dict) and 'index' in v:v['index']+=offsets['textures']
                else:remap_textures(v)
        remap_textures(m)
    for m in other.get('meshes',[]):
        for p in m['primitives']:
            p['attributes']={k:v+offsets['accessors'] for k,v in p['attributes'].items()}
            if 'indices' in p:p['indices']+=offsets['accessors']
            if 'material' in p:p['material']+=offsets['materials']
    for s in other.get('skins',[]):
        s['joints']=[n+offsets['nodes'] for n in s['joints']]
        if 'skeleton' in s:s['skeleton']+=offsets['nodes']
        if 'inverseBindMatrices' in s:s['inverseBindMatrices']+=offsets['accessors']
    for i,n in enumerate(other['nodes']):
        n['name']=f'{namespace}_{i}_{n.get("name", "node")}'
        if 'children' in n:n['children']=[v+offsets['nodes'] for v in n['children']]
        for k in ['mesh','skin']:
            if k in n:n[k]+=offsets[k+'es' if k=='mesh' else 'skins']
    for k in offsets:doc[k].extend(other.get(k,[]))
    doc['scenes'][0]['nodes'].extend(n+offsets['nodes'] for n in other['scenes'][0]['nodes'])
    return offsets['nodes']

def interpolate(times,values,t,method,rotation):
    idx=np.maximum(0,np.searchsorted(times,t,side='right')-1);nxt=np.minimum(idx+1,len(times)-1)
    span=times[nxt]-times[idx];u=np.clip((t-times[idx])/np.where(span==0,1,span),0,1)[:,None]
    if method=='CUBICSPLINE':
        a,b=values[idx*3+1],values[nxt*3+1]
        result=(2*u**3-3*u**2+1)*a+(u**3-2*u**2+u)*span[:,None]*values[idx*3+2]+(-2*u**3+3*u**2)*b+(u**3-u**2)*span[:,None]*values[nxt*3]
    elif method=='STEP':result=values[idx]
    else:
        a,b=values[idx],values[nxt]
        if rotation:b=np.where((a*b).sum(axis=1)[:,None]<0,-b,b)
        result=a*(1-u)+b*u
    if rotation:result/=np.maximum(np.linalg.norm(result,axis=1)[:,None],1e-12)
    return result

def bake(doc,data,source,raw,track,node_map,duration,animation):
    segments=sorted(track['clips'],key=lambda c:c['start']);channels={}
    for segment in segments:
        for offset in [track.get('position'),track.get('rotation'),segment.get('offset'),segment.get('rotation')]:
            if offset and any(abs(v)>1e-5 for v in offset.values()):raise ValueError('Nonzero timeline offset requires explicit composition')
        clip=next((a for a in source.get('animations',[]) if a['name'].split('--')[0]==segment['name']),None)
        if not clip:
            metadata=source['scenes'][0].get('extras',{}).get('BAAD_unity_animation',{}).get('clips',[])
            if any(c['name']==segment['name'] for c in metadata):continue
            raise ValueError('Animation export missing '+segment['name'])
        for channel in clip['channels']:
            key=(node_map[channel['target']['node']],channel['target']['path'])
            sampler=clip['samplers'][channel['sampler']]
            channels.setdefault(key,[]).append((segment,sampler))
    for (node,kind),items in channels.items():
        if kind=='weights':raise ValueError('Morph timeline requires verification')
        times=np.unique(np.array([0.,duration]+[i/30 for i in range(math.ceil(duration*30))]+[max(0,c['start']) for c,_ in items]+[min(duration,c['start']+c['duration']) for c,_ in items]))
        size=4 if kind=='rotation' else 3
        values=np.tile(np.array(doc['nodes'][node].get(kind,{'rotation':[0,0,0,1],'translation':[0,0,0],'scale':[1,1,1]}[kind])),(len(times),1)).astype(float)
        # Timeline pre-roll must hold the first authored pose. A late first
        # clip otherwise exposes the prefab's standing bind pose every loop.
        first,first_sampler=items[0]
        if first['start']>0:
            pre=times<first['start']
            st=np.array(read_accessor(source,raw,first_sampler['input']))[:,0]
            sv=np.array(read_accessor(source,raw,first_sampler['output']))
            values[pre]=interpolate(st,sv,np.full(int(pre.sum()),first['clipIn']),first_sampler.get('interpolation','LINEAR'),kind=='rotation')
        for k,(segment,sampler) in enumerate(items):
            start=max(0,segment['start']);end=items[k+1][0]['start'] if k+1<len(items) else duration+1
            mask=(times>=start-1e-8)&(times<end-1e-8 if k+1<len(items) else times<=end)
            local=(np.minimum(times[mask],segment['start']+segment['duration'])-segment['start'])*segment['speed']+segment['clipIn']
            st=np.array(read_accessor(source,raw,sampler['input']))[:,0];sv=np.array(read_accessor(source,raw,sampler['output']))
            values[mask]=interpolate(st,sv,local,sampler.get('interpolation','LINEAR'),kind=='rotation')
        assert np.isfinite(values).all()
        ai=append_accessor(doc,data,[(float(t),) for t in times],'SCALAR');doc['accessors'][ai]['min']=[float(times[0])];doc['accessors'][ai]['max']=[float(times[-1])]
        bi=append_accessor(doc,data,values.tolist(),'VEC4' if size==4 else 'VEC3')
        animation['channels'].append({'sampler':len(animation['samplers']),'target':{'node':node,'path':kind}})
        animation['samplers'].append({'input':ai,'output':bi,'interpolation':'LINEAR'})

def timeline_metadata(body,track,key):
    metadata=body['scenes'][0]['extras']['BAAD_unity_animation']['clips']
    combined={'track':key,'name':key,'events':[],'unity_curves':[]}
    for segment in track['clips']:
        source=next(c for c in metadata if c['name']==segment['name'])
        for event in source.get('events',[]):
            time=(event['time']-segment['clipIn'])/segment['speed']
            if 0<=time<=segment['duration']:combined['events'].append({**event,'time':time+segment['start']})
    combined['unity_curves']=boolean_curves(metadata,track)
    combined['events'].sort(key=lambda e:e['time'])
    return combined

results=[];bychar={}
for profile in profiles:
    pack=profile['character'];target=character_root/pack
    manifest=bychar.setdefault(pack,json.loads((target/'character.json').read_text(encoding='utf8')))
    if not any(r['character']==pack for r in results) and not append_only:manifest['furniture']=[]
    manifest.setdefault('furniture',[])
    if append_only and any(f.get('sourceTimeline')==profile['icon'] and f.get('sourceGroup')==profile['group'] and f.get('sourceStudentTrack')==profile['studentTrack']['name'] for f in manifest['furniture']):continue
    record={'character':pack,'furnitureId':profile['furnitureId'],'group':profile['group'],'studentTrack':profile['studentTrack']['name']}
    try:
        partners=[]
        for student in profile['participants']:
            if profile['studentTrack']['name'].split('_')[0]==student:continue
            suffix=profile['studentTrack']['name'].partition('_')[2]
            partner=next((p for p in all_profiles if p['icon']==profile['icon'] and p['group']==profile['group'] and p['studentTrack']['name']==student+('_'+suffix if suffix else '')),None)
            if not partner:raise ValueError('Required partner model not installed: student '+student)
            partners.append(partner)
        # Some cafe-only prefabs contain furniture-specific geometry absent
        # from the regular character. The offline profile can supply its
        # separately adapted body, without replacing ordinary action assets.
        body_model=R/profile['bodyModel'] if profile.get('bodyModel') else target/'model.glb'
        doc,data=load(body_model);body,bdata=exported(profile['root']);furn,fdata=exported(profile['icon'])
        body_geometry=restore_geometry(doc,data,{n:r for n,r,_ in renderers(prefab(profile['root']))},{},restore_static=False)
        fdefaults=adapt_furniture(furn,fdata,profile['icon'])
        base=len(doc['nodes']);merge(doc,data,furn,fdata)
        names={n.get('name'):i for i,n in enumerate(doc['nodes'][:base])}
        mapping={i:names[n['name']] for i,n in enumerate(body['nodes']) if n.get('name') in names}
        duration=max(c['start']+c['duration'] for t in [profile['studentTrack']]+profile['furnitureTracks'] for c in t['clips'])
        key=f"f{profile['furnitureId']}_{len(manifest['furniture'])}"
        animation={'name':key,'channels':[],'samplers':[]}
        bake(doc,data,body,bdata,profile['studentTrack'],mapping,duration,animation)
        for track in profile['furnitureTracks']:bake(doc,data,furn,fdata,track,{i:i+base for i in range(len(furn['nodes']))},duration,animation)
        if len({(c['target']['node'],c['target']['path']) for c in animation['channels']})!=len(animation['channels']):raise ValueError('Overlapping furniture animation bindings')
        combined=timeline_metadata(body,profile['studentTrack'],key)
        extras=doc['scenes'][0]['extras'];oldvis=extras.get('BA_pet_visibility',{'defaults':{},'clips':{}});extras['BAAD_unity_animation']={'clips':[combined],'schema_version':0}
        renderer_list=[n for n,_,_ in renderers(prefab(profile['root']))]
        layouts={'aoba':{2:'CH0288_Face_Outline',3:'CH0288_Face01_Outline',4:'CH0288_Face02_Outline'},'junko_newyear':{9:'CH0192_Body_Face01_Outline',10:'CH0192_Body_Face_Outline'},'reisa':{5:'CH0167_Body_Face01_Outline',6:'CH0167_Body_Face_Outline'},'koyuki':{3:'CH0198_Face01_Outline',4:'CH0198_Face_Outline'},'koyuki_pajamas':{4:'CH0310_Face01_Mesh',5:'CH0310_Face02_Mesh'}}
        for i,n in layouts.get(pack,{}).items():
            while len(renderer_list)<=i:renderer_list.append('')
            renderer_list[i]=n
        # The cafe-only Otogi prefab adds the strategy-table prop omitted by
        # the ordinary combat prefab. Its authored event retains index 10.
        if profile['root']=='CH0174_CafeOnly':
            while len(renderer_list)<=10:renderer_list.append('')
            renderer_list[10]='my_event091_strategytable_prop_03'
        attach_visibility(doc,renderer_event_layout(pack,renderer_list),ignore_missing=pack=='toki',ignored_events=[{'clip':key,'index':10,'function':'AniEvt_DisableChildRenderer','time':0}] if pack=='otogi' else [])
        if pack=='yakumo' and profile['icon']=='my_event086_salesdesk':
            # This cafe scene holds the original physical phone for its full
            # sequence. Do not let the legacy renderer-index event remove it
            # while the separately controlled screen FX continue to play.
            phone=next(i for i,n in enumerate(doc['nodes']) if n.get('name')=='CH0228_Prop03_Outline' and 'mesh'in n)
            extras['BA_pet_visibility']['clips'][key]=[t for t in extras['BA_pet_visibility']['clips'][key] if t['node']!=phone]
        extras['BA_pet_visibility']['defaults']=oldvis['defaults']
        # Original idle defaults hide weapons and alternate faces before the
        # furniture clip's own visibility events are applied.
        for tr in oldvis['clips'].get(manifest['animations']['idle'],[]):
            if tr['keys']:extras['BA_pet_visibility']['defaults'][str(tr['node'])]=tr['keys'][0][1]
        for i,n in enumerate(furn['nodes']):
            name=n.get('name','');original=name if name in fdefaults else re.sub(r'_\d+$','',name)
            if original in fdefaults:extras['BA_pet_visibility']['defaults'][str(base+i)]=fdefaults[original]
        for partner in partners:
            partner_manifest=json.loads((character_directory(partner['character'])/'character.json').read_text(encoding='utf8'))
            pd,pb=load(character_directory(partner['character'])/'model.glb')
            restore_geometry(pd,pb,{n:r for n,r,_ in renderers(prefab(partner['root']))},{},restore_static=False)
            ps,psb=exported(partner['root'])
            offset=merge(doc,data,pd,pb,'partner_'+partner['character'])
            pnames={n.get('name'):i+offset for i,n in enumerate(pd['nodes'])}
            pmap={i:pnames[n['name']] for i,n in enumerate(ps['nodes']) if n.get('name') in pnames}
            bake(doc,data,ps,psb,partner['studentTrack'],pmap,duration,animation)
            pm=timeline_metadata(ps,partner['studentTrack'],key)
            px=pd['scenes'][0]['extras'];pv=px.get('BA_pet_visibility',{'defaults':{},'clips':{}})
            px['BAAD_unity_animation']={'clips':[pm]}
            attach_visibility(pd,renderer_event_layout(partner['character'],[n for n,_,_ in renderers(prefab(partner['root']))]))
            for tr in pv['clips'].get(partner_manifest['animations']['idle'],[]):
                if tr['keys']:pv['defaults'][str(tr['node'])]=tr['keys'][0][1]
            extras['BA_pet_visibility']['defaults'].update({str(int(i)+offset):v for i,v in pv['defaults'].items()})
            extras['BA_pet_visibility']['clips'][key].extend({**t,'node':t['node']+offset} for t in px['BA_pet_visibility']['clips'][key])
            if px.get('BA_halo_follow'):
                h=px['BA_halo_follow'];extras.setdefault('BA_halo_follow_extra',[]).append({**h,'node':h['node']+offset,'target':h['target']+offset})
            if partner_manifest.get('mouth'):
                m=partner_manifest['mouth'];extras.setdefault('BA_furniture_mouths',[]).append({**m,'events':{key:mouth_events(pm,m['defaultTile'])}})
        extras['BA_furniture']={'id':profile['furnitureId'],'group':profile['group'],'sourceTimeline':profile['icon'],'duration':duration}
        timeline = next((clip['name'] for track in profile['furnitureTracks'] for clip in track['clips']
                         if clip['name'] == 'my_hotsprings_01_woodenbathtub_CH0123'), None)
        apply_prop_visibility(doc, pack, timeline)
        doc['animations']=[animation];doc['extensionsUsed']=list(set(doc.get('extensionsUsed',[])+['KHR_materials_unlit']))
        events=mouth_events(combined,manifest.get('mouth',{}).get('defaultTile',0))
        filename=key+'.glb';save(target/filename,doc,compact(doc,data))
        title=profile['name']+('（多人）' if len(partners)>1 else '（双人）' if partners else '')
        if '_' in profile['studentTrack']['name']:title+=' · 动作 '+str(int(profile['studentTrack']['name'].split('_')[-1])+1)
        manifest['furniture'].append({'id':key,'name':title,'model':filename,'clip':key,'duration':duration,'mouthEvents':events,**({'note':'与'+ '、'.join(json.loads((character_directory(p['character'])/'character.json').read_text(encoding='utf8'))['name'] for p in partners)+'同步互动。'} if partners else {})})
        manifest['furniture'][-1].update(yaw=math.pi*character_view_yaws.get(pack,{}).get(key,view_yaws.get(str(profile['furnitureId']),.75)),sourceTimeline=profile['icon'],sourceGroup=profile['group'],sourceStudentTrack=profile['studentTrack']['name'])
        record.update(status='ready',model=filename,duration=duration,channels=len(animation['channels']),geometry=furn.get('extras',{}).get('BA_geometry_repairs',{}),bodyGeometry=body_geometry)
        print('READY',pack,key,round(duration,2),flush=True)
    except Exception as error:
        import traceback;traceback.print_exc()
        record.update(status='pending',reason=str(error));print('PENDING',pack,profile['furnitureId'],str(error),flush=True)
    results.append(record)
for pack,manifest in bychar.items():(character_root/pack/'character.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf8')
report=pathlib.Path(os.environ.get('BA_FURNITURE_REPORT',W/'furniture-adaptation.json'))
if requested and report.exists():results=[r for r in json.loads(report.read_text(encoding='utf8')) if r['character'] not in requested]+results
report.write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf8')
