"""Repair source-material/event bindings without replacing any animation curves."""
import copy,json,pathlib,shutil
from glb import load,save,read_accessor,append_accessor,append_view
from mouth_events import mouth_events
from visibility import attach_visibility

R=pathlib.Path(__file__).resolve().parents[1];W=R/'.assets'
evidence=json.loads((R/'test-results/visual-triage-source-1029.json').read_text('utf8'))
output=W/'repair-2026-10-29';results=[]
for pack in ['tsurugi']:
    source=R/'characters'/pack;target=output/pack
    shutil.copytree(source,target,dirs_exist_ok=True)
    manifest=json.loads((target/'character.json').read_text('utf8'))
    doc,binary=load(source/'model.glb');animations=copy.deepcopy(doc['animations'])
    if pack=='aoba':
        names=[r['renderer'] for r in evidence[pack]['renderers']]
        layout={2:'CH0288_Face_Outline',3:'CH0288_Face01_Outline',4:'CH0288_Face02_Outline'}
        for i,name in layout.items():names[i]=name
        previous=doc['scenes'][0]['extras']['BA_pet_visibility']
        defaults={doc['nodes'][int(i)]['name']:value for i,value in previous['defaults'].items()}
        attach_visibility(doc,names,defaults)
        doc.setdefault('extras',{})['BA_renderer_event_layout']={str(i):n for i,n in layout.items()}
    elif pack=='neru_uniform':
        source_material=next(m for r in evidence[pack]['renderers'] for m in r['materials'] if m['name']=='CH0280_Hair_Alpha')
        assert source_material['floats']['_SrcBlend']==5 and source_material['floats']['_DstBlend']==10
        material=next(m for m in doc['materials'] if m['name']==source_material['name'])
        material.update(alphaMode='BLEND',doubleSided=source_material['floats']['_Cull']==0)
    else:
        original=next(m for r in evidence[pack]['renderers'] for m in r['materials'] if m['name']=='Tsurugi_Original_Eyemouth')
        atlas=next(t for t in original['textures'] if t['slot']=='_MouthTileTex')
        image=len(doc['images']);doc['images'].append({'bufferView':append_view(doc,binary,(W/'visual-triage-1029'/atlas['file']).read_bytes()),'mimeType':'image/png'})
        texture=len(doc['textures']);doc['textures'].append({'source':image})
        material=len(doc['materials']);doc['materials'].append({'name':'Tsurugi_Original_Mouth','pbrMetallicRoughness':{'baseColorTexture':{'index':texture}},'extensions':{'KHR_materials_unlit':{}},'doubleSided':True,'alphaMode':'MASK','alphaCutoff':.1})
        uv0=evidence[pack]['defaultUV'];sx,sy=atlas['scale'];count=0
        for mesh in doc['meshes']:
            for eye in list(mesh['primitives']):
                if doc['materials'][eye['material']]['name']!=original['name']:continue
                uv=read_accessor(doc,binary,eye['attributes']['TEXCOORD_0'])
                indices=[v[0] for v in read_accessor(doc,binary,eye['indices'])]
                adjacency={}
                for i in range(0,len(indices),3):
                    triangle=indices[i:i+3]
                    for v in triangle:adjacency.setdefault(v,set()).update(triangle)
                unseen=set(indices);vertices=set()
                while unseen:
                    group=set();todo=[next(iter(unseen))]
                    while todo:
                        v=todo.pop()
                        if v in group:continue
                        group.add(v);todo.extend(adjacency[v]-group)
                    unseen-=group
                    if all(uv[v][0]<=.2501 and uv[v][1]>=.7499 for v in group):vertices.update(group)
                mouth_ids=[];eye_ids=[]
                for i in range(0,len(indices),3):
                    triangle=indices[i:i+3]
                    (mouth_ids if all(v in vertices for v in triangle) else eye_ids).extend((v,) for v in triangle)
                if not mouth_ids:continue
                mouth=copy.deepcopy(eye)
                if eye_ids:eye['indices']=append_accessor(doc,binary,eye_ids,'SCALAR',5123)
                else:mesh['primitives'].remove(eye)
                mouth['indices']=append_accessor(doc,binary,mouth_ids,'SCALAR',5123)
                mouth['attributes']['TEXCOORD_0']=append_accessor(doc,binary,[(u*sx+uv0['x'],v*sy+1-sy-uv0['y']) for u,v in uv],'VEC2')
                mouth['material']=material;mesh['primitives'].append(mouth);count+=len(mouth_ids)//3
        assert count>0,'Original mouth island missing'
        cols=round(original['floats']['_MouthTileCols']);rows=round(original['floats']['_MouthTileRows'])
        tile=round(uv0['y']*rows)*100+round(uv0['x']*cols)
        clips=doc['scenes'][0]['extras']['BAAD_unity_animation']['clips']
        manifest['mouth']={'material':'Tsurugi_Original_Mouth','defaultTile':tile,'columns':cols,'rows':rows,'events':{c['track']:mouth_events(c,tile) for c in clips}}
    assert animations==doc['animations'],'Animation curves must remain unchanged'
    save(target/'model.glb',doc,binary)
    (target/'character.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf8')
    results.append({'character':pack,'animationsUnchanged':len(animations),'actions':len(manifest['actions'])})
(R/'test-results/visual-repairs-2026-10-29.json').write_text(json.dumps(results,indent=2),'utf8')
print(results)
