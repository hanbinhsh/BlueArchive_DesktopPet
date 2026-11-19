"""Verify original meshes/animation data survive the furniture FX adaptation."""
import json,pathlib,hashlib,os
from glb import load,read_accessor

root=pathlib.Path(os.environ.get('BA_CHARACTERS','characters'))
previous=pathlib.Path('release/v0.2.11/win-unpacked/resources/characters')
rows=[]
def geometry(doc,binary):
    result=[]
    for mesh in doc.get('meshes',[]):
        primitives=[]
        for p in mesh['primitives']:
            m=doc['materials'][p['material']]
            if m.get('extras',{}).get('BA_cafeParticle'):continue
            primitives.append({'material':m.get('name'),'attributes':{k:read_accessor(doc,binary,v) for k,v in p['attributes'].items()},'indices':read_accessor(doc,binary,p['indices']) if 'indices' in p else None,'targets':[{k:read_accessor(doc,binary,v) for k,v in t.items()} for t in p.get('targets',[])]})
        if primitives:result.append(primitives)
    return result
def animations(doc,binary):
    return [{'name':a['name'],'channels':a['channels'],'samplers':[{**s,'input':read_accessor(doc,binary,s['input']),'output':read_accessor(doc,binary,s['output'])} for s in a['samplers']]} for a in doc.get('animations',[])]
for manifest in sorted(root.glob('*/character.json')):
    char=json.loads(manifest.read_text('utf8'))
    for model in sorted({f['model'] for f in char.get('furniture',[])}):
        path=manifest.parent/model;old=previous/manifest.parent.name/model
        d,b=load(path);a,c=load(old)
        assert geometry(d,b)==geometry(a,c),str(path)+' original geometry differs'
        assert animations(d,b)==animations(a,c),str(path)+' original animation differs'
        rows.append({'character':manifest.parent.name,'model':model,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'geometryUnchanged':True,'animationUnchanged':True,'particles':sum(bool(m.get('extras',{}).get('BA_cafeParticle')) for m in d['materials'])})
pathlib.Path('test-results/particle-renderer032.json').write_text(json.dumps(rows,indent=2),'utf8')
print('Preserved original geometry and animation:',len(rows))
