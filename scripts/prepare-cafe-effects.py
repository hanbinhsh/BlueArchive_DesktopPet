"""Attach original timeline effects as local GLB nodes with bounded particle data.

The runtime evaluates the authored deterministic burst curves. Unsupported
random shapes/emission are reported rather than replaced with fabricated art.
"""
import pathlib,json,sys,copy,math,shutil,io,hashlib,random,re,os
import numpy as np
from PIL import Image
from particle_emission import emission_times,burst_times,limit_births
from glb import load,save,append_accessor,append_view,compact
from static_fx_meshes import attach_static_particles
from fx_hierarchy import annotate,reparent
from nested_fx import window_control

W=pathlib.Path('.assets');fxdir=pathlib.Path(os.environ.get('BA_FX_SOURCE',str(W/'cafe-fx')));source=json.loads((fxdir/'source.json').read_text('utf8'))
profiles=json.loads((W/'furniture-profiles.json').read_text('utf8'))
root=pathlib.Path(os.environ.get('BA_FX_STAGE',str(W/'pending-repairs')));root.mkdir(parents=True,exist_ok=True);report=[]
requested=sys.argv[1:] or ['akane_uniform','mine','kikyou_swimsuit','aris','neru','midori','momoi','hifumi_racing','azusa_racing']
shader_kinds={'FX_SHADER_Explosion_Smoke_Distortion_0':'smokeDistortion','FX_SHADER_Step_2side_0':'stepTwoSide','FX_SHADER_Explosion_Smoke_Blur_Flowmap_0':'flowmap','General Unlit Texture':'unlit','General Unlit VC-Texture':'unlitVC','FX_SHADER_AlphaBlend_Add_Double_Distort_Sp_1a':'doubleSoft','FX_SHADER_AlphaBlend_Add_Distort_Sp_0':'distortSoft','FX_SHADER_Explosion_Smoke_Blur_1a':'cloudNoDepth','FX_SHADER_Water_Distortion_0':'water','FX_SHADER_Water_Distortion_Blur_0':'waterBlur','FX_SHADER_Step_Distort_1a':'step1','FX_SHADER_Two_Step_Distort_0':'twoStep','FX_SHADER_AlphaBlend_Add':'blend','FX_SHADER_AlphaBlend_Add_Mask_0':'mask','FX_SHADER_AlphaBlend_Add_Distort_0':'distort','FX_SHADER_AlphaBlend_Add_Distort_1a':'distort1','FX_SHADER_Step_0':'step','FX_SHADER_Multiplicative_0':'multiply','FX_SHADER_Additive_0':'add','FX_SHADER_Main_Add_Channel_Distort_1a':'channel','FX_SHADER_Main_Add_Channel_Distort_0':'classic'}
shader_kinds['FX_SHADER_Matcap']='matcap'
shader_kinds['FX_SHADER_Matcap_0']='matcapBlend'
shader_kinds['FX_SHADER_AlphaBlend_Add_Double_Distort_1a']='doubleDistort'
shader_kinds['C-Weapon']='unlit'
allowed=['InitialModule','SizeModule','RotationModule','ColorModule','UVModule','VelocityModule','CustomDataModule','ShapeModule','ClampVelocityModule','SubModule']
def curve(c):
    d={k:v for k,v in c.items() if k in ['minMaxState','scalar','minScalar']}
    for k in ['maxCurve','minCurve']:
        if c.get(k,{}).get('m_Curve'):
            d[k]=copy.deepcopy(c[k])
            # Unity uses infinite slopes for stepped keys. JSON cannot contain
            # Infinity; null is the explicit step sentinel understood at runtime.
            for key in d[k]['m_Curve']:
                for slope in ['inSlope','outSlope']:
                    if slope in key and not math.isfinite(key[slope]):key[slope]=None
    return d
def trim(value):
    if isinstance(value,float) and not math.isfinite(value):return None
    if isinstance(value,list):return [trim(v) for v in value]
    if not isinstance(value,dict):return value
    if 'minMaxState' in value and 'scalar' in value:return curve(value)
    return {k:trim(v) for k,v in value.items()}
for character in requested:
    target=root/character
    if not target.exists():shutil.copytree(pathlib.Path('characters')/character,target)
    manifest=json.loads((target/'character.json').read_text('utf8'))
    for furniture in manifest.get('furniture',[]):
        # Work from a pristine model for repeatable adaptation. Staged racing
        # furniture has no installed counterpart and is backed up on first run.
        backup=W/'cafe-fx/base'/character/furniture['model'];backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists():shutil.copyfile(target/furniture['model'],backup)
        doc,binary=load(target/furniture['model'] if os.environ.get('BA_FX_APPEND')=='1' else backup);extra=doc['scenes'][0].get('extras',{}).get('BA_furniture',{})
        icon=furniture.get('sourceTimeline',extra.get('sourceTimeline'));group=furniture.get('sourceGroup',extra.get('group'))
        timeline=next((t for t in source['timelines'] if t['icon']==icon),None)
        if not timeline:continue
        controls=[c for c in timeline['controls'] if c['parents'] and c['parents'][0]==group]
        material_templates={m['name']:copy.deepcopy(m) for m in doc['materials'] if m.get('name')}
        entry={'character':character,'furniture':furniture['id'],'particles':0,'omitted':[]};texture_cache={};mesh_cache={}
        def texture(t,alpha_from_red=False,white_rgb=False):
            cache_key=(t['file'],tuple(t.get('wrap',[0,0])),alpha_from_red,white_rgb)
            if cache_key in texture_cache:return texture_cache[cache_key]
            raw=(fxdir/t['file']).read_bytes()
            if alpha_from_red or white_rgb:
                pixels=np.array(Image.open(io.BytesIO(raw)).convert('RGBA'))
                if alpha_from_red:pixels[:,:,3]=pixels[:,:,0]
                if white_rgb:pixels[:,:,:3]=255
                png=io.BytesIO();Image.fromarray(pixels).save(png,format='PNG');raw=png.getvalue()
            image=len(doc.setdefault('images',[]));doc['images'].append({'bufferView':append_view(doc,binary,raw),'mimeType':'image/png'})
            sampler=len(doc.setdefault('samplers',[]));wrap=lambda n:10497 if n==0 else 33648 if n==2 else 33071
            doc['samplers'].append({'wrapS':wrap(t.get('wrap',[0,0])[0]),'wrapT':wrap(t.get('wrap',[0,0])[1])})
            index=len(doc.setdefault('textures',[]));doc['textures'].append({'source':image,'sampler':sampler});texture_cache[cache_key]=index;return index
        def visit(n,parent,control,active=True,triggered=False,level=0,spawn=None,root_clock=None):
            root_clock=root_clock or control
            if n.get('activationWindows'):
                for window in n['activationWindows']:
                    scoped=window_control(control,root_clock,window)
                    if scoped is None:continue
                    clone={**n,'active':True};clone.pop('activationWindows')
                    visit(clone,parent,scoped,active,triggered,level,spawn,root_clock)
                return
            if level>8:raise ValueError("Cyclic sub-emitter graph")
            if n.get("particleId") in sub_targets and not triggered:return
            active=active and bool(n['active'])
            index=len(doc['nodes']);x,y,z=n['position'];qx,qy,qz,qw=n['rotation']
            doc['nodes'].append({'name':f'cafe_fx_{index}_{n["name"]}','translation':[-x,y,z],'rotation':[qx,-qy,-qz,qw],'scale':n['scale'],'children':[]})
            if n.get('objectId'):doc['nodes'][index]['extras']={'BA_sourceObjectId':n['objectId']}
            doc['nodes'][parent].setdefault('children',[]).append(index)
            if spawn:doc['nodes'][index].setdefault('extras',{})['BA_subEmitter']=spawn
            p=n.get('particle');renderer=n.get('renderer',{})
            if active and p and p['EmissionModule']['enabled'] and renderer.get('m_RenderMode') in [0,1,2,4] and (n.get('materials') or n.get('missing')):
                original_shader=n.get('materials',[{}])[0].get('shader') if n.get('materials') else None
                template=material_templates.get(n['materials'][0]['name']) if original_shader in ['MX/E-Standard','MX/C-Weapon'] else None
                if original_shader=='Universal Render Pipeline/Particles/Unlit':
                    original=n['materials'][0];flags=original['floats']
                    main=next((t for t in original['textures'] if t['slot']=='_BaseMap' and 'file' in t),None)
                    # URP's ordinary multiply-color alpha particle, without
                    # distortion, soft-depth fading or flipbook interpolation.
                    if main and flags.get('_ColorMode',0)==0 and flags.get('_SrcBlend')==5 and flags.get('_DstBlend')==10 and not any(flags.get(k,0) for k in ['_AlphaClip','_DistortionEnabled','_SoftParticlesEnabled','_CameraFadingEnabled','_FlipbookBlending']):
                        template={'pbrMetallicRoughness':{'baseColorTexture':{'index':texture(main)},'baseColorFactor':original['colors'].get('_BaseColor',[1,1,1,1]),'metallicFactor':0,'roughnessFactor':1},'alphaMode':'BLEND','doubleSided':flags.get('_Cull',2)==0,'extensions':{'KHR_materials_unlit':{}},'extras':{'BA_surfaceAdaptation':'original-urp-unlit-alpha'}}
                if template is None and original_shader in ['MX/E-Standard','MX/E-Standard-FX']:
                    original=n['materials'][0]
                    main=next((t for t in original['textures'] if t['slot']=='_MainTex' and 'file' in t),None)
                    # These opaque ice meshes use no distortion or UV motion.
                    # Adapt their original diffuse surface by the same unlit
                    # convention as the surrounding furniture (not URP lighting).
                    if main and not any(v for k,v in original['floats'].items() if ('Speed' in k or 'Distortion_Power' in k or k=='_Custom_Data_Offset_Use')):
                        template={'pbrMetallicRoughness':{'baseColorTexture':{'index':texture(main)},'baseColorFactor':original['colors'].get('_BaseColor',[1,1,1,1]),'metallicFactor':0,'roughnessFactor':1},'alphaMode':'OPAQUE','doubleSided':original['floats'].get('_Cull',2)==0,'extensions':{'KHR_materials_unlit':{}},'extras':{'BA_surfaceAdaptation':'original-diffuse'}}
                reason=None
                trail=p.get('TrailModule',{})
                # Native stationary local particles leave world-space ribbons
                # as their animated emitter moves (the cauldron ladle).
                supported_trail=trail.get('enabled') and trail.get('mode')==0 and trail.get('worldSpace') and trail.get('ratio')==1 and not any(trail.get(k) for k in ['sizeAffectsWidth','sizeAffectsLifetime','inheritParticleColor']) and trail['lifetime']['minMaxState']==0 and p['moveWithTransform']==0 and not p['ShapeModule']['enabled'] and not p['VelocityModule']['enabled'] and p['InitialModule']['startSpeed']['minMaxState']==0 and p['InitialModule']['startSpeed']['scalar']==0 and len(n.get('materials',[]))==2 and n['materials'][1]['shader']=='DSFX/FX_SHADER_AlphaBlend_Add' and not n['materials'][1]['textures']
                if supported_trail:
                    initial=p['InitialModule']
                    supported_trail=not p['looping'] and trail['minVertexDistance']==0 and all(v['minMaxState']==0 for v in [initial['startLifetime'],initial['gravityModifier'],p['startDelay']]) and initial['gravityModifier']['scalar']==0 and renderer.get('m_Enabled')is not False
                if p['ShapeModule']['enabled'] and p['ShapeModule']['type'] not in [0,2,4,5,8,10,12,16]:reason='unsupported emission shape'
                elif renderer.get('m_RenderAlignment') not in [0,1,2,3,4] or (renderer.get('m_RenderMode')==4 and renderer.get('m_RenderAlignment') not in [0,1,2,3,4]):reason='unsupported particle alignment'
                elif renderer['m_RenderMode']==1 and renderer['m_CameraVelocityScale']:reason='unsupported camera-motion stretch'
                elif not n.get('materials'):reason='missing original material'
                elif any('missing' in t for t in n['materials'][0].get('textures',[])):reason='missing original texture'
                elif template is None and n['materials'][0]['shader'].rsplit('/',1)[-1] not in shader_kinds and n['materials'][0]['shader'] not in ['DSFX/FX_SHADER_AlphaBlend_0','DSFX/FX_SHADER_Step_Distort_0','DSFX/FX_SHADER_Explosion_Smoke_Blur_Sp_1a','DSFX/FX_SHADER_Smoke_SmoothStep_0','DSFX/FX_SHADER_Explosion_Smoke_Blur_0','DSFX/FX_SHADER_Explosion_Smoke_0']:reason='unsupported original shader '+n['materials'][0]['shader']
                elif p['EmissionModule']['rateOverTime']['minMaxState'] not in [0,1,3]:reason='unsupported random-curve continuous emission'
                elif p['ClampVelocityModule']['enabled'] and (p['ClampVelocityModule']['separateAxis'] or p['ClampVelocityModule']['inWorldSpace']):reason='unsupported velocity limit space'
                elif any('Smoke' in m['shader'] and m['shader'].rsplit('/',1)[-1] not in shader_kinds and m['shader'] not in ['DSFX/FX_SHADER_Explosion_Smoke_Blur_Sp_1a','DSFX/FX_SHADER_Smoke_SmoothStep_0','DSFX/FX_SHADER_Explosion_Smoke_Blur_0','DSFX/FX_SHADER_Explosion_Smoke_0'] for m in n.get('materials',[])):reason='unsupported original smoke shader'
                for mod,value in p.items():
                    if isinstance(value,dict) and value.get('enabled') and mod.endswith('Module') and mod not in allowed+['EmissionModule','ShapeModule'] and not(mod=='TrailModule'and supported_trail):reason='unsupported '+mod
                if reason:entry['omitted'].append({'node':n['path'],'reason':reason})
                else:
                    original=n['materials'][0];tex=next((t for slot in ['_Texture','_Tex_Main','_MainTex','_BaseMap','_Tex_Mask'] for t in original['textures'] if t['slot']==slot and 'file' in t),None)
                    schedule=[]
                    # Expand finite timeline bursts, including one authored prewarm
                    # cycle. Keep overlapping generations when lifetime > period.
                    shaped=p['ShapeModule']['enabled'] or bool(p['EmissionModule']['rateOverTime']['scalar']) or (p['EmissionModule']['rateOverTime']['minMaxState']==3 and bool(p['EmissionModule']['rateOverTime']['minScalar']))
                    seed=int.from_bytes(hashlib.sha256((n['path']+str(p.get('randomSeed') or control.get('seed',0))).encode()).digest()[:4],'little')
                    rng=random.Random(seed)
                    persistent=bool(control.get('existing')) and not control.get('restartOnActivation',False)
                    first_generation=-1 if p.get('prewarm') else 0
                    last_generation=math.ceil(((control['duration']*control['speed']+control['clipIn'])*p['simulationSpeed'])/p['lengthInSec'])
                    if persistent and shaped and p['looping']:
                        lifetime=p['InitialModule']['startLifetime']
                        if lifetime['minMaxState'] not in [0,3]:raise ValueError('Persistent curved particle lifetime needs a bounded pool')
                        last_generation=math.ceil(max(lifetime['scalar'],lifetime['minScalar'])/p['lengthInSec'])+1
                    recycle_period=(last_generation-first_generation)*p['lengthInSec']
                    generations=range(first_generation,last_generation) if shaped and p['looping'] else [0]
                    for generation in generations:
                        for burst in p['EmissionModule'].get('m_Bursts',[]):
                            count=burst['countCurve']
                            if count['minMaxState'] not in [0,3]:entry['omitted'].append({'node':n['path'],'reason':'curved burst count'});continue
                            for burst_time in burst_times(burst,p['lengthInSec']):
                                if rng.random()>burst['probability']:continue
                                total=round(rng.uniform(count['minScalar'],count['scalar'])) if count['minMaxState']==3 else round(count['scalar'])
                                for ordinal in range(min(128,total)):
                                    schedule.append((generation*p['lengthInSec']+burst_time,ordinal,total,rng.getrandbits(32)))
                    rate=p['EmissionModule']['rateOverTime']['scalar']
                    if rate or p['EmissionModule']['rateOverTime']['minMaxState'] in [1,3]:
                        end=(control['duration']*control['speed']+control['clipIn'])*p['simulationSpeed'] if p['looping'] else p['lengthInSec']
                        if persistent and shaped and p['looping']:end=last_generation*p['lengthInSec']
                        begin=-p['lengthInSec'] if p.get('prewarm') else 0
                        for birth in emission_times(p['EmissionModule']['rateOverTime'],begin,end,p['lengthInSec'],seed=seed):
                            schedule.append((birth,0,1,rng.getrandbits(32)))
                    if any(b['cycleCount']==0 for b in p['EmissionModule'].get('m_Bursts',[])):
                        if p.get('ringBufferMode',0):
                            if p.get('ringBufferMode',0)==2 and p['InitialModule']['maxNumParticles']==1:
                                schedule=schedule[:1]
                            else:
                                raise ValueError('Indefinite burst with ring-buffer reuse requires explicit support')
                    # Continuous emitters share the same particle capacity as
                    # bursts. A one-slot LED at 120 births/s must not become
                    # thousands of coincident, overbright draw calls.
                    if not p.get('ringBufferMode',0) and p['InitialModule']['startLifetime']['minMaxState'] in [0,3]:
                        init_cap=p['InitialModule']
                        if (init_cap['maxNumParticles']>1 and p['EmissionModule']['rateOverTime']['minMaxState']==0 and p['EmissionModule']['rateOverTime']['scalar']>=1000
                            and not any(p[m]['enabled'] for m in ['ShapeModule','VelocityModule','ColorModule','SizeModule','RotationModule'])
                            and init_cap['startSpeed']['minMaxState']==0 and init_cap['startSpeed']['scalar']==0
                            and init_cap['gravityModifier']['minMaxState']==0 and init_cap['gravityModifier']['scalar']==0
                            and all(init_cap[k]['minMaxState']==0 for k in ['startLifetime','startSize','startRotation','startColor'])
                            and (not p['UVModule']['enabled'] or p['UVModule']['frameOverTime']['minMaxState']==0)
                            and original['shader']=='DSFX/FX_SHADER_AlphaBlend_0' and original['colors'].get('_Color',[1,1,1,1])[3]>=0.99):
                            init_cap={**init_cap,'maxNumParticles':1}
                        schedule=limit_births(schedule,init_cap,p['startDelay'])
                    for birth,ordinal,total,particle_seed in schedule:
                            mat=len(doc['materials']);name=f'cafe_particle_{mat}'
                            spec={'clip':furniture['clip'],'control':control,'particle':trim({k:p[k] for k in allowed if k in p}),
                                'sourceName':n['path'],'simulationSpeed':p['simulationSpeed'],'simulationSpace':p.get('moveWithTransform',0),'renderer':{k:renderer.get(k,0) for k in ['m_Enabled','m_RenderMode','m_RenderAlignment','m_SortingOrder','m_SortingFudge','m_LengthScale','m_VelocityScale','m_CameraVelocityScale','m_Flip','m_ApplyActiveColorSpace','m_VertexStreams','m_UseCustomVertexStreams']},
                                'emissionPeriod':p['lengthInSec'],'initialTime':(birth%p['lengthInSec'])/p['lengthInSec'],'persistent':persistent,'delay':curve(p['startDelay']),'burst':birth,'seed':particle_seed,'ordinal':ordinal,'burstCount':total,'loop':p['looping'] and (persistent or not shaped),'period':recycle_period if persistent and shaped and p['looping'] else p['lengthInSec'],'ringMode':p.get('ringBufferMode',0),'ringRange':p.get('ringBufferLoopRange',{'x':0,'y':1}),
                                'material':trim({k:v for k,v in original.items() if k!='textures'})}
                            if control.get('propertyClock'):spec['propertyClock']=control['propertyClock']
                            depth=bool(original['floats'].get('_ZWrite_Mode',original['floats'].get('_ZWrite',0)))
                            material={'name':name,'pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'metallicFactor':0,'roughnessFactor':1},'alphaMode':'BLEND','doubleSided':True,'extensions':{'KHR_materials_unlit':{}},'extras':{'BA_maskedFx':True,'BA_depthWrite':depth,'BA_cafeParticle':spec}}
                            if icon=='my_event088_retractwindow' and 'retractwindow_BG' in n['path'] and not depth:
                                # Reuse the original window-hole mask. The desktop has
                                # no surrounding cafe walls to hide off-window FX.
                                material['extras']['BA_clipStencil']=7
                            if template is not None:
                                metadata=material['extras'];material=copy.deepcopy(template);material['name']=name;material.setdefault('extras',{}).update(metadata)
                                material['extras']['BA_depthWrite']=template.get('alphaMode','OPAQUE')!='BLEND'
                                spec['surfaceTint']=original['colors'].get('_BaseColor',[1,1,1,1]) if original_shader=='Universal Render Pipeline/Particles/Unlit' else template.get('pbrMetallicRoughness',{}).get('baseColorFactor',[1,1,1,1])
                                if original_shader=='Universal Render Pipeline/Particles/Unlit':
                                    # glTF factors are bounded; preserve the HDR
                                    # particle tint in the runtime specification.
                                    material['pbrMetallicRoughness']['baseColorFactor']=[max(0,min(1,v)) for v in spec['surfaceTint']]
                                spec['texture']={k:v for k,v in tex.items() if k not in ['file','missing']} if tex else None
                            elif tex:
                                alpha_from_red=not original['floats'].get('_RGBRGBA',0) if 'Main_Add_Channel' not in original['shader'] else not original['floats'].get('_Main_Tex_Alpha_use',0)
                                white_rgb=original['shader']=='DSFX/FX_SHADER_AlphaBlend_0' and bool(original['floats'].get('_Main_Texture_No',0))
                                material['pbrMetallicRoughness']['baseColorTexture']={'index':texture(tex,alpha_from_red,white_rgb)}
                                spec['texture']={k:v for k,v in tex.items() if k not in ['file','missing']}
                            if original['shader']=='DSFX/FX_SHADER_Step_Distort_0':
                                water={'kind':'step','floats':original['floats'],'color':original['colors']['_Color'],'uvAddST':original['colors'].get('_UV_Add_TilingOffset',[0,0,0,0])}
                                for slot,key in [('_Tex_Main','mainTexture'),('_Tex_Mask','maskTexture'),('_Tex_Distort','distortTexture')]:
                                    t=next((t for t in original['textures'] if t['slot']==slot and 'file' in t),None)
                                    if not t:continue
                                    tex_entry={'index':texture(t),'st':t['scale']+t['offset']}
                                    if key in ('maskTexture','distortTexture') and t.get('srgb') and original['floats'].get('_Step_Scroll_Use'):tex_entry['srgb']=True
                                    water[key]=tex_entry
                                material['extras']['BA_waterFx']=water
                            if original['shader'].rsplit('/',1)[-1] in shader_kinds or original['shader'] in ['DSFX/FX_SHADER_Explosion_Smoke_Blur_Sp_1a','DSFX/FX_SHADER_Smoke_SmoothStep_0','DSFX/FX_SHADER_Explosion_Smoke_Blur_0','DSFX/FX_SHADER_Explosion_Smoke_0']:
                                fx={'kind':shader_kinds.get(original['shader'].rsplit('/',1)[-1]) or ('cloud' if 'Blur_Sp' in original['shader'] else 'puff' if 'Blur_0' in original['shader'] else 'pixel' if original['shader'].endswith('Explosion_Smoke_0') else 'smooth'),'floats':dict(original['floats']),'colors':dict(original['colors'])}
                                properties=json.loads((W/'carrier-shaders'/(original['shader'].rsplit('/',1)[-1]+'.json')).read_text('utf8'))['m_PropInfo']['m_Props']
                                declared={prop['m_Name'] for prop in properties}
                                fx['floats']={k:v for k,v in fx['floats'].items() if k in declared}
                                fx['colors']={k:v for k,v in fx['colors'].items() if k in declared}
                                for prop in properties:
                                    if prop['m_Type'] in [0,1]:fx['colors'].setdefault(prop['m_Name'],[prop['m_DefValue['+str(i)+']'] for i in range(4)])
                                    elif prop['m_Type'] in [2,3]:fx['floats'].setdefault(prop['m_Name'],prop['m_DefValue[0]'])
                                for slot,key in [('_Texture','mainTexture'),('_MainTex','mainTexture'),('_MainTexRGBA','mainTexture'),('_FlowTexRGB','distortTexture'),('_Tex_Main','mainTexture'),('_Tex_MainRGB','mainTexture'),('_Tex_DistortRG','distortTexture'),('_Main_TexRGBA','mainTexture'),('_Tex_Mask','maskTexture'),('_Sub_Tex','maskTexture'),('_Tex_Distort','distortTexture'),('_Tex_RDistortGDissolve','dissolveTexture')]:
                                    t=next((t for t in original['textures'] if t['slot']==slot and 'file' in t),None)
                                    if t:
                                        tex_entry={'index':texture(t),'st':t['scale']+t['offset']}
                                        if fx['kind']=='step' and key=='maskTexture' and t.get('srgb'):tex_entry['srgb']=True
                                        fx[key]=tex_entry
                                if fx['kind'] in ('matcap','matcapBlend'):
                                    for slot,key in [('_Main_Tex','mainTexture'),('_Matcap_Tex','maskTexture')]:
                                        t=next((t for t in original['textures'] if t['slot']==slot and 'file'in t),None)
                                        if t:fx[key]={'index':texture(t),'st':t['scale']+t['offset']}
                                material['extras']['BA_smokeFx']=fx
                            doc['materials'].append(material)
                            mesh=n.get('mesh') if renderer['m_RenderMode']==4 else None
                            if mesh and renderer.get('m_RenderAlignment')==2 and original['shader']=='DSFX/FX_SHADER_AlphaBlend_0':
                                # Native phone-screen meshes retain their own
                                # winding. Unlike generated sprite quads, they
                                # use the source shader's ordinary back culling.
                                material['doubleSided']=original['floats'].get('_Cull_Mode',2)==0
                            if mesh:
                                material['extras']['BA_nativeMeshPivot']=True
                                pivot=renderer.get('m_Pivot',{'x':0,'y':0,'z':0});extent=[max(v[i] for v in mesh['positions'])-min(v[i] for v in mesh['positions']) for i in range(3)]
                                # Native Unity BakeMesh applies mesh pivot Z with
                                # the opposite sign to X/Y (see unity036 probe).
                                positions=[[(v[i]+pivot['xyz'[i]]*extent[i]*(-1 if i==2 else 1))*(-1 if i==0 else 1) for i in range(3)] for v in mesh['positions']];uv=[[v[0],1-v[1]] for v in mesh['uv']];indices=[(v,) for sub in mesh['triangles'] for tri in sub for v in reversed(tri)]
                            else:
                                positions=[[.5,-.5,0],[-.5,-.5,0],[-.5,.5,0],[.5,.5,0]];uv=[[0,1],[1,1],[1,0],[0,0]];indices=[(i,) for i in [2,1,0,3,2,0]]
                            if not mesh:
                                pivot=renderer.get('m_Pivot',{'x':0,'y':0,'z':0});positions=[[v[0]-pivot['x'],v[1]+pivot['y'],v[2]+pivot['z']] for v in positions]
                            # Unity permits identically named siblings (e.g. the
                            # two arcade health bars). A hierarchy path is not
                            # an object identity: their pivots/meshes may differ.
                            geometry_key=n.get('particleId') or id(n)
                            if geometry_key not in mesh_cache:
                                attrs={'POSITION':append_accessor(doc,binary,positions,'VEC3'),'TEXCOORD_0':append_accessor(doc,binary,uv,'VEC2')}
                                if mesh and mesh.get('normals'):
                                    attrs['NORMAL']=append_accessor(doc,binary,[[-v[0],v[1],v[2]] for v in mesh['normals']],'VEC3')
                                if mesh and mesh.get('uv2'):
                                    attrs['TEXCOORD_1']=append_accessor(doc,binary,[[v[0],1-v[1]] for v in mesh['uv2']],'VEC2')
                                if mesh and mesh.get('colors'):
                                    # MeshHandler exposes packed Color32 channels as bytes
                                    # on these source meshes. glTF float colors are 0..1.
                                    colors=mesh['colors']
                                    if any(v>1 for color in colors for v in color):
                                        if any(v<0 or v>255 for color in colors for v in color):raise ValueError('Invalid source vertex color')
                                        colors=[[v/255 for v in color] for color in colors]
                                    attrs['COLOR_0']=append_accessor(doc,binary,colors,'VEC4')
                                doc['accessors'][attrs['POSITION']].update(min=[min(v[i] for v in positions) for i in range(3)],max=[max(v[i] for v in positions) for i in range(3)])
                                mesh_cache[geometry_key]=(dict(attrs),append_accessor(doc,binary,indices,'SCALAR',5125))
                            attrs,index_accessor=mesh_cache[geometry_key]
                            mi=len(doc['meshes']);doc['meshes'].append({'primitives':[{'attributes':dict(attrs),'indices':index_accessor,'material':mat}]})
                            ni=len(doc['nodes']);doc['nodes'].append({'name':name,'mesh':mi,'extras':{'BA_cafeParticle':True}});doc['nodes'][index]['children'].append(ni);entry['particles']+=1
                            if supported_trail:
                                tm=len(doc['materials']);trail_material=copy.deepcopy(n['materials'][1])
                                doc['materials'].append({'name':name+'_trail','pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'metallicFactor':0,'roughnessFactor':1},'alphaMode':'BLEND','doubleSided':True,'extensions':{'KHR_materials_unlit':{}},'extras':{'BA_maskedFx':True,'BA_depthWrite':False,'BA_cafeTrail':{'sourceParticle':name,'spec':copy.deepcopy(spec),'trail':trim(trail),'material':trim(trail_material)}}})
                                ti=len(doc['meshes']);doc['meshes'].append({'primitives':[{'attributes':{'POSITION':append_accessor(doc,binary,[[0,0,0]]*3,'VEC3')},'indices':append_accessor(doc,binary,[[0],[1],[2]],'SCALAR',5125),'material':tm}]})
                                tn=len(doc['nodes']);doc['nodes'].append({'name':name+'_trail','mesh':ti,'extras':{'BA_cafeTrail':True}});doc['nodes'][index]['children'].append(tn)
                            for sub in n.get('subEmitters',[]):
                                child_initial=sub_nodes[sub['target']]['particle']['InitialModule']
                                constant_initial=all(v.get('minMaxState') in ([0,2,4] if k=='startColor' else [0,3]) for k,v in child_initial.items() if isinstance(v,dict) and 'minMaxState' in v)
                                if sub['type'] not in [0,2] or (sub['properties'] and (sub['type']!=0 or not constant_initial)):
                                    entry['omitted'].append({'node':n['path'],'reason':'unsupported sub-emitter inheritance/event'});continue
                                if rng.random()>sub['probability']:continue
                                child=copy.deepcopy(sub_nodes[sub['target']]);reparent(child,n);child['active']=True
                                visit(child,index,copy.deepcopy(control),active,True,level+1,{'parent':name,'event':sub['type'],'properties':sub['properties']&31},root_clock)
            for child in n['children']:visit(child,index,control,active,root_clock=root_clock)
        for control in controls:
            effect=source['effects'].get(control['prefab'])
            if not effect:entry['omitted'].append({'node':control['prefab'],'reason':'source prefab incomplete'});continue
            effect=copy.deepcopy(effect)
            attach_static_particles(effect,control['duration']*control['speed']+control['clipIn'])
            if control.get('existing'):
                effect=copy.deepcopy(effect)
                effect.update(position=[0,0,0],rotation=[0,0,0,1],scale=[1,1,1],active=True)
            control={**control,'binding':control['binding'].strip('[]')}
            candidates=[i for i,n in enumerate(doc['nodes']) if n.get('name')==control['binding'] or re.fullmatch(r'furniture_\d+_'+re.escape(control['binding']),n.get('name',''))]
            if not candidates:
                candidates=[i for i,n in enumerate(doc['nodes']) if n.get('name','').endswith('_'+control['binding'])]
            # Exposed references in the furniture prefab refer to its own rig,
            # not to a same-named character bone imported into the merged GLB.
            furniture_candidates=[i for i in candidates if re.fullmatch(r'furniture_\d+_'+re.escape(control['binding']),doc['nodes'][i].get('name',''))]
            if len(furniture_candidates)==1:candidates=furniture_candidates
            if len(candidates)>1:
                # Skinned render meshes are flattened into additional root
                # nodes. Exposed GameObjects refer to the original transform.
                transforms=[i for i in candidates if 'mesh' not in doc['nodes'][i]]
                if len(transforms)==1:candidates=transforms
            if not candidates and not control.get('existing') and control.get('exposedReference') in [0,'0'] and control.get('bindingResolved') is False:
                # Unity PrefabControlPlayable permits an unparented instance.
                # Furniture-local world space is the prefab root in our merged
                # scene; never apply this fallback to an unresolved named ref.
                candidates=[i for i,n in enumerate(doc['nodes']) if n.get('name')=='furniture_0_'+icon]
            candidates=[i for i in candidates if not doc['nodes'][i].get('extras',{}).get('BA_exportPlaceholder')]
            if len(candidates)!=1:entry['omitted'].append({'node':control['prefab'],'reason':'ambiguous/missing binding '+control['binding']});continue
            sub_nodes={};sub_targets=set()
            def registry(n):
                if n.get('particleId'):sub_nodes[n['particleId']]=n
                for sub in n.get('subEmitters',[]):sub_targets.add(sub['target'])
                for child in n['children']:registry(child)
            annotate(effect);registry(effect)
            missing=sub_targets-set(sub_nodes)
            if missing:raise ValueError('Missing sub-emitter nodes: '+str(missing))
            visit(effect,candidates[0],control)
        save(target/furniture['model'],doc,compact(doc,binary));report.append(entry);print(character,furniture['id'],entry['particles'],'omitted',len(entry['omitted']),flush=True)
pathlib.Path(os.environ.get('BA_FX_REPORT','test-results/cafe-fx-adaptation.json')).write_text(json.dumps(report,indent=2),'utf8')
