"""Recover the community-extracted CH0284 tracks onto the verified official rig.

Only matching bone TRS channels are imported. Mouth tile meshes are discarded in
favor of the original game's atlas events already exported from its clips.
"""
import copy,hashlib,json,pathlib,sys
import httpx
from glb import load,save,append_view
R=pathlib.Path(__file__).resolve().parents[1];W=R/'.assets'
rows=json.loads((R/'test-results/wiki-model-inventory.json').read_text(encoding='utf8'))
natsu='--natsu' in sys.argv
prefix='CH0221_NonWeapon' if natsu else 'CH0284'
slug='natsu-nonweapon' if natsu else 'yuuka-pajama'
entry=next(r for r in rows if r['filename']==('Natsu (Band) (No Weapon).glb' if natsu else 'Yuuka (Pajama).glb'))
path=W/f'wiki-{slug}.glb'
if not path.exists():
    response=httpx.get(entry['url'],timeout=90,follow_redirects=True);response.raise_for_status();path.write_bytes(response.content)
reference,data=load(path)
source=next((W/('exported/natsu_band_relax' if natsu else 'exported/yuuka_pajama-focused')).rglob(prefix+'.glb'))
doc,binary=load(source);names={n['name']:i for i,n in enumerate(doc['nodes'])}
if natsu:
    import UnityPy
    env=UnityPy.load(*map(str,[p for p in (W/'selected').glob('*.bundle') if 'ch0221' in p.name and 'animationclips' in p.name]))
    metadata=[]
    for obj in env.objects:
        if obj.type.name!='AnimationClip':continue
        clip=obj.read_typetree()
        if not clip['m_Name'].startswith(prefix+'_'):continue
        metadata.append({'name':clip['m_Name'],'track':clip['m_Name'],'collection':obj.assets_file.name,'path_id':obj.path_id,
            'sample_rate':clip['m_SampleRate'],'wrap_mode':clip['m_WrapMode'],'humanoid_baked':False,'unity_curves':[],'object_curves':[],
            'events':[{'time':e['time'],'function':e['functionName'],'int':e['intParameter'],'float':e['floatParameter'],'string':e['data']} for e in clip['m_Events']]})
    doc['scenes'][0].setdefault('extras',{})['BAAD_unity_animation']={'schema_version':0,'clips':metadata}
clips=doc['scenes'][0]['extras']['BAAD_unity_animation']['clips']
doc['animations']=[];views={};accessors={};report=[]
def accessor(i):
    if i in accessors:return accessors[i]
    a=copy.deepcopy(reference['accessors'][i]);assert 'sparse' not in a
    v=a['bufferView'];view=reference['bufferViews'][v];start=view.get('byteOffset',0)
    if v not in views:views[v]=append_view(doc,binary,data[start:start+view['byteLength']])
    a['bufferView']=views[v];accessors[i]=len(doc['accessors']);doc['accessors'].append(a);return accessors[i]
for original in reference['animations']:
    if natsu and original['name'] not in ['Idle','Stretching']:
        report.append({'clip':original['name'],'imported':False,'reason':'Requires the corresponding scene furniture'});continue
    match=[c for c in clips if c['name'].lower()==prefix.lower()+'_'+original['name'].lower()]
    if not match:
        report.append({'clip':original['name'],'imported':False,'reason':'No corresponding original event metadata'});continue
    animation=copy.deepcopy(original);animation['name']=match[0]['track'];channels=[];excluded=[]
    for channel in animation['channels']:
        node=reference['nodes'][channel['target']['node']];name=node['name']
        if name.startswith('Mouth_'):
            excluded.append(name);continue
        assert name in names,(original['name'],name)
        actual=doc['nodes'][names[name]]
        for prop,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:
            assert max(abs(a-b) for a,b in zip(node.get(prop,default),actual.get(prop,default)))<1e-5,(name,prop)
        channel['target']['node']=names[name];channels.append(channel)
    animation['channels']=channels
    for s in animation['samplers']:
        for field in ['input','output']:s[field]=accessor(s[field])
    doc['animations'].append(animation)
    report.append({'clip':match[0]['name'],'imported':True,'channels':len(channels),'discardedMouthMeshes':sorted(set(excluded))})
dest=W/('exported/natsu_nonweapon-restored' if natsu else 'exported/yuuka_pajama-restored');dest.mkdir(exist_ok=True)
save(dest/(prefix+'.glb'),doc,binary)
evidence={'reference':entry['url'],'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'officialBase':str(source.relative_to(R)),'tracks':report}
(R/f'test-results/{slug}-reference-recovery.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
print('Recovered',len(doc['animations']),'tracks; verified identical local bind transforms')
