"""Check original face tracks, their skin influences, events and pickup loops."""
import pathlib,json,UnityPy,sys
from glb import load,read_accessor
ROOT=pathlib.Path(__file__).resolve().parents[1]
env=UnityPy.load(*map(str,(ROOT/'.assets/selected').glob('*.bundle')))
loops={}
for obj in env.objects:
    if obj.type.name=='AnimationClip':
        raw=obj.read_typetree()
        if 'Formation_Pickup' in raw.get('m_Name',''):
            loops[raw['m_Name']]=bool(raw.get('m_MuscleClip',{}).get('m_LoopTime'))
report=[]
for path in (ROOT/'characters').glob('*/model.glb'):
    if sys.argv[1:] and path.parent.name not in sys.argv[1:]:continue
    doc,binary=load(path); influences={}
    for node in doc['nodes']:
        if 'skin' not in node or 'mesh' not in node:continue
        joints=doc['skins'][node['skin']]['joints']
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            attrs=primitive['attributes']
            for js,ws in zip(read_accessor(doc,binary,attrs['JOINTS_0']),read_accessor(doc,binary,attrs['WEIGHTS_0'])):
                for joint,weight in zip(js,ws):
                    if weight>0: influences[joints[joint]]=influences.get(joints[joint],0)+1
    clips=[]
    for anim in doc['animations']:
        groups={'brows':set(),'eyes':set(),'mouthBones':set(),'morphs':set()}
        for channel in anim['channels']:
            index=channel['target']['node'];name=doc['nodes'][index]['name'];sampler=anim['samplers'][channel['sampler']]
            values=read_accessor(doc,binary,sampler['output'])
            if sampler.get('interpolation')=='CUBICSPLINE':values=values[1::3]
            varying=any(max(v[i] for v in values)-min(v[i] for v in values)>1e-4 for i in range(len(values[0])))
            if not varying:continue
            for key,terms in [('brows',['brow','blow']),('eyes',['eye']),('mouthBones',['mouth'])]:
                if any(t in name.lower() for t in terms) and influences.get(index,0):groups[key].add(name)
            if channel['target']['path']=='weights':groups['morphs'].add(name)
        meta=next(c for c in doc['scenes'][0]['extras']['BAAD_unity_animation']['clips'] if c['track']==anim['name'])
        clips.append({'clip':anim['name'],'varyingSkinnedFaceBones':{k:sorted(v) for k,v in groups.items()},'mouthEvents':sum(e['function'] in ('SetMouthTile','SetHorizontallyFlippedMouthTile','SetMouthTileToDefault') for e in meta['events']),'visibilityCurves':sum(c['attribute'] in ('m_Enabled','m_IsActive') for c in meta['unity_curves']),'otherCurves':[c['attribute'] for c in meta['unity_curves'] if c['attribute'] not in ('m_Enabled','m_IsActive')],'originalPickupLoop':loops.get(meta['name'])})
    report.append({'character':path.parent.name,'clips':clips})
used_pickups=[(r['character'],c) for r in report for c in r['clips'] if 'Formation_Pickup' in c['clip']]
assert len(used_pickups)>=5
assert all(c['originalPickupLoop'] is True for _,c in used_pickups), [(name,c['clip'],c['originalPickupLoop']) for name,c in used_pickups if c['originalPickupLoop'] is not True]
(ROOT/'test-results/expression-source.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(len(report), 'packs audited;',len(used_pickups),'installed original pickup loops verified')
