"""Preserve the Carrier's own idle on the matching white-outfit rig."""
import copy,json,pathlib
from glb import load,save,append_view,compact
from mouth_events import mouth_events
from visibility import attach_visibility
R=pathlib.Path(__file__).resolve().parents[1];folder=R/'.assets/expanded-ready/kei_story'
source=next((R/'.assets/exported/costume-variants').rglob('CH0335_Carrier.glb'))
raw,data=load(source);doc,binary=load(folder/'model.glb');manifest=json.loads((folder/'character.json').read_text(encoding='utf8'))
animation=copy.deepcopy(raw['animations'][0]);meta=next(c for c in raw['scenes'][0]['extras']['BAAD_unity_animation']['clips'] if c['track']==animation['name'])
assert meta['name']=='CH0335_Carrier_Idle'
assert not any(a['id']=='original_carrier_idle' for a in manifest['actions'])
for c in animation['channels']:
    original=raw['nodes'][c['target']['node']]
    matches=[i for i,n in enumerate(doc['nodes']) if n.get('name')==original.get('name') and ('mesh' in n)==('mesh' in original)]
    assert len(matches)==1,original['name']
    target=doc['nodes'][matches[0]]
    for field,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:
        assert max(abs(a-b) for a,b in zip(original.get(field,default),target.get(field,default)))<1e-5,(original['name'],field)
    c['target']['node']=matches[0]
accessors={};views={}
for sampler in animation['samplers']:
    for field in ['input','output']:
        i=sampler[field]
        if i not in accessors:
            a=copy.deepcopy(raw['accessors'][i]);v=a['bufferView'];view=raw['bufferViews'][v];start=view.get('byteOffset',0)
            if v not in views:views[v]=append_view(doc,binary,data[start:start+view['byteLength']])
            a['bufferView']=views[v];accessors[i]=len(doc['accessors']);doc['accessors'].append(a)
        sampler[field]=accessors[i]
trial={'nodes':doc['nodes'],'scenes':[{'extras':{'BAAD_unity_animation':{'clips':[meta]}}}]};attach_visibility(trial,[])
extras=doc['scenes'][0]['extras'];extras['BAAD_unity_animation']['clips'].append(meta)
extras['BA_pet_visibility']['clips'].update(trial['scenes'][0]['extras']['BA_pet_visibility']['clips'])
doc['animations'].append(animation)
manifest['mouth']['events'][meta['track']]=mouth_events(meta,manifest['mouth']['defaultTile'])
manifest['actions'].append({'id':'original_carrier_idle','label':'白色剧情服 · 携带待机','clip':meta['track'],'category':'剧情','sourceName':meta['name']})
save(folder/'model.glb',doc,compact(doc,binary));(folder/'character.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
(R/'test-results/kei-carrier-idle.json').write_text(json.dumps({'source':str(source.relative_to(R)),'clip':meta['name'],'channels':len(animation['channels']),'bindTransformsMatch':True},indent=2),encoding='utf8')
print('Verified matching rig; added original Carrier idle')
