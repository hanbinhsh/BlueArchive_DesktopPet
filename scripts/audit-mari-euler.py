"""Ensure every original Mari Euler binding has an exported rotation channel."""
import json,pathlib,zlib,UnityPy
from glb import load
root=pathlib.Path(__file__).resolve().parents[1]
doc,binary=load(root/'characters/mari/model.glb')
parents={child:index for index,node in enumerate(doc['nodes']) for child in node.get('children',[])}
def path(index):
    names=[]
    while index in parents:
        names.append(doc['nodes'][index]['name']);index=parents[index]
    return '/'.join(reversed(names))
hashes={zlib.crc32(path(i).encode()):i for i in range(len(doc['nodes']))}
env=UnityPy.load(*map(str,(root/'.assets/selected').glob('*mari_original*.bundle')))
report=[]
for obj in env.objects:
    if obj.type.name!='AnimationClip':continue
    source=obj.read_typetree()
    animation=next((a for a in doc['animations'] if a['name'].split('--')[0]==source['m_Name']),None)
    if animation is None:continue
    eulers=[b for b in source['m_ClipBindingConstant']['genericBindings'] if b['typeID']==4 and b['attribute']==4]
    targets={c['target']['node'] for c in animation['channels'] if c['target']['path']=='rotation'}
    for binding in eulers:
        assert binding['path'] in hashes, binding
        assert hashes[binding['path']] in targets, path(hashes[binding['path']])
    report.append({'clip':source['m_Name'],'originalEulerBindings':len(eulers),'exportedRotationChannels':len(targets)})
assert len(report)==4
(root/'test-results/mari-euler-audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
