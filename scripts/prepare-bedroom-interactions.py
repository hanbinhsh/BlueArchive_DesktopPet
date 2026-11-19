"""Compose the seven authored bedroom character/furniture timeline pairs."""
import ast,copy,io,json,math,re,shutil
from pathlib import Path
import numpy as np
import UnityPy
from glb import load,save,append_view,append_accessor,read_accessor,compact
from furniture_geometry import restore_geometry
from mouth_events import mouth_events
from rigid_geometry import rebuild_rigid_mesh
from UnityPy.helpers.MeshHelper import MeshHandler
R=Path(__file__).resolve().parents[1];W=R/'.assets'
# Reuse the existing reviewed material and timeline composition functions,
# without executing the cafe batch at module scope.
names={'renderers','adapt_furniture','merge','interpolate','bake','timeline_metadata'}
module=ast.parse((R/'scripts/prepare-furniture.py').read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'prepare-furniture-functions','exec'))
deps=json.loads((W/'bedroom-dependencies.json').read_text())
deps['dependencies'].update(json.loads((W/'bedroom-texture-dependencies.json').read_text())['dependencies'])
env=UnityPy.load(*[str(W/'selected'/n) for n in deps['dependencies']])
gos={o.path_id:o.read() for o in env.objects if o.type.name=='GameObject' and o.assets_file.name.lower()=='cab-58a8b7ad1cdfaf7a2e253a3964cbf674'}
prefabs={'Bed':gos[4113871467935940421],'Windowsofa':gos[2340516510502862661]}
def prefab(name):return prefabs[name]
rawdoc,rawbin=load(next((W/'bedroom-exported').rglob('field_833_zone01.glb')))
target=W/'scene-repair-ready/hina_pajamas';shutil.copytree(R/'characters/hina_pajamas',target,dirs_exist_ok=True)
manifest=json.loads((target/'character.json').read_text(encoding='utf8'));manifest['furniture']=[]
body,bodybin=load(target/'model.glb');timelines=json.loads((W/'bedroom-timelines.json').read_text());report=[]
def furniture(kind):
    d=copy.deepcopy(rawdoc);data=bytearray(rawbin);root=next(i for i,n in enumerate(d['nodes']) if n.get('name')==f'Prop_Field_833_Zone01_{kind}_Mesh')
    keep=set()
    def add(i):
        keep.add(i)
        for child in d['nodes'][i].get('children',[]):add(child)
    add(root)
    for i,n in enumerate(d['nodes']):
        if 'skin' in n and set(d['skins'][n['skin']]['joints'])<=keep:keep.add(i)
    order=sorted(keep);nm={old:new for new,old in enumerate(order)};d['nodes']=[d['nodes'][i] for i in order]
    meshids=sorted({n['mesh'] for n in d['nodes'] if 'mesh' in n});mm={old:new for new,old in enumerate(meshids)}
    skinids=sorted({n['skin'] for n in d['nodes'] if 'skin' in n});sm={old:new for new,old in enumerate(skinids)}
    d['meshes']=[d['meshes'][i] for i in meshids];d['skins']=[d['skins'][i] for i in skinids]
    for n in d['nodes']:
        if 'children' in n:n['children']=[nm[i] for i in n['children']]
        if 'mesh' in n:n['mesh']=mm[n['mesh']]
        if 'skin' in n:n['skin']=sm[n['skin']]
    for s in d['skins']:
        s['joints']=[nm[i] for i in s['joints']]
        if 'skeleton' in s:s['skeleton']=nm[s['skeleton']]
    d['scenes']=[{'nodes':[nm[root]]+[i for i,n in enumerate(d['nodes']) if 'skin' in n],'extras':copy.deepcopy(rawdoc['scenes'][0]['extras'])}]
    d['scene']=0;d['animations']=[a for a in d['animations'] if a['name'].startswith(f'Prop_Field_833_Zone01_{kind}_')]
    for a in d['animations']:
        for c in a['channels']:c['target']['node']=nm[c['target']['node']]
    # Whole-scene export suffixes colliding bone names. Restore only names
    # confirmed by this furniture's original skin, preserving numbered bones.
    sourcebones={b.read().m_GameObject.read().m_Name for _,r,_ in renderers(prefab(kind)) if hasattr(r,'m_Bones') for b in r.m_Bones}
    for n in d['nodes']:
        name=n.get('name','');base=re.sub(r'_\d+$','',name)
        if name not in sourcebones and base in sourcebones:n['name']=base
    if kind=='Bed':
        renderer=next(r for _,r,_ in renderers(prefab(kind)) if hasattr(r,'m_Bones'))
        source=MeshHandler(renderer.m_Mesh.read());source.process()
        node=next(n for n in d['nodes'] if 'skin' in n)
        jointnames=[d['nodes'][i]['name'] for i in d['skins'][node['skin']]['joints']]
        remap=[jointnames.index(b.read().m_GameObject.read().m_Name) for b in renderer.m_Bones]
        rebuild_rigid_mesh(d,data,node,renderer,source,remap,weighted=True)
    defaults=adapt_furniture(d,data,kind)
    # Bedroom props were authored for a fixed camera. Desktop rotation exposes
    # the reverse of their single-sheet headboards, curtains and cushions.
    for material in d['materials']:material['doubleSided']=True
    return d,compact(d,data),defaults
furnitures={kind:furniture(kind) for kind in ['Bed','Windowsofa']}
for suffix,label in [('Bed_Day00_Ing','卧室床 · 坐卧'),('Bed_Day01_Ing','卧室床 · 安睡'),('Bed_Day02_Ing','卧室床 · 翻身'),('Bed_Day03_Ing','卧室床 · 坐姿'),('Windowsofa_Start','窗边沙发 · 坐下'),('Windowsofa_Ing','窗边沙发 · 休息'),('Windowsofa_End','窗边沙发 · 起身')]:
    row=next(t for t in timelines if t['timeline']=='Prop_Field_833_Zone01_'+suffix)
    student=next(t for t in row['tracks'] if t['name'].startswith('Field_Player'))
    kind='Bed' if suffix.startswith('Bed') else 'Windowsofa';furn,fdata,defaults=furnitures[kind]
    ft=[t for t in row['tracks'] if t['binding'] and t['binding'].endswith(f'Prop_Field_833_Zone01_{kind}_Mesh')]
    track={'name':'combined','clips':[c for t in ft for c in t['clips']]}
    duration=max(c['start']+c['duration'] for t in [student,*ft] for c in t['clips'])
    key='bedroom_'+suffix.lower();doc=copy.deepcopy(body);data=bytearray(bodybin);offset=merge(doc,data,furn,fdata)
    animation={'name':key,'channels':[],'samplers':[]}
    bake(doc,data,body,bodybin,student,{i:i for i in range(len(body['nodes']))},duration,animation)
    bake(doc,data,furn,fdata,track,{i:i+offset for i in range(len(furn['nodes']))},duration,animation)
    assert len({(c['target']['node'],c['target']['path']) for c in animation['channels']})==len(animation['channels'])
    extra=doc['scenes'][0]['extras'];combined=timeline_metadata(body,student,key)
    oldvis=extra.get('BA_pet_visibility',{'defaults':{},'clips':{}})
    sourceclip=student['clips'][0]['name'];sourceanim=next(a['name'] for a in body['animations'] if a['name'].split('--')[0]==sourceclip)
    extra['BA_pet_visibility']={'defaults':oldvis['defaults'],'clips':{key:oldvis['clips'].get(sourceanim,[])}}
    extra['BAAD_unity_animation']={'schema_version':0,'clips':[combined]}
    for i,n in enumerate(furn['nodes']):
        name=n.get('name','');name=name if name in defaults else re.sub(r'_\d+$','',name)
        if name in defaults:extra['BA_pet_visibility']['defaults'][str(i+offset)]=defaults[name]
    extra['BA_furniture']={'id':key,'sourceTimeline':row['timeline'],'duration':duration}
    doc['animations']=[animation];doc['extensionsUsed']=list(set(doc.get('extensionsUsed',[])+['KHR_materials_unlit']))
    filename=key+'.glb';save(target/filename,doc,compact(doc,data))
    manifest['furniture'].append({'id':key,'name':label,'model':filename,'clip':key,'duration':duration,'mouthEvents':mouth_events(combined,manifest['mouth']['defaultTile']),'yaw':math.pi*(1.25 if kind=='Bed' else .75),'note':'原版卧室场景，人物与家具按同一时间轴播放。'})
    report.append({'id':key,'sourceTimeline':row['timeline'],'student':student,'furniture':ft,'duration':duration})
    print(key,duration,'ready',flush=True)
manifest['actions']=[a for a in manifest['actions'] if 'Cafe_Prop_Field_833_' not in a['clip']]
manifest['note']='场景中的睡衣外观。床与窗边沙发的七项原版动作在下方“家具互动”中播放。没有提起动作，拖动时保持待机。'
manifest['source']['description']=manifest['source']['description'].split(' Bedroom furniture and synchronized timelines:')[0]+' Bedroom furniture and synchronized timelines: official Field833/Zone01 Bed and Windowsofa. Double-sided surfaces support desktop rotation.'
manifest.pop('framing',None)
(target/'character.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
(R/'test-results/bedroom-composition.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
