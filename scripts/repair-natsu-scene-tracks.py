"""Replace recovered community tracks with explicitly bound official clips."""
import copy,json,shutil,hashlib
from pathlib import Path
from glb import load,save,append_view,compact,read_accessor
R=Path(__file__).resolve().parents[1];W=R/'.assets';key='natsu_band_relax'
source=next((W/'exported/natsu-scene-original').rglob('CH0221_NonWeapon.glb'));original,raw=load(source)
target=W/'scene-repair-ready'/key;shutil.copytree(R/'characters'/key,target,dirs_exist_ok=True)
doc,data=load(target/'model.glb');c=json.loads((target/'character.json').read_text(encoding='utf8'))
names={}
for i,n in enumerate(doc['nodes']):names.setdefault(n.get('name'),[]).append(i)
amap={};vmap={};report=[]
def acc(index):
    if index in amap:return amap[index]
    a=copy.deepcopy(original['accessors'][index]);v=a['bufferView'];view=original['bufferViews'][v]
    if v not in vmap:
        start=view.get('byteOffset',0);vmap[v]=append_view(doc,data,raw[start:start+view['byteLength']],view.get('target'))
        if 'byteStride' in view:doc['bufferViews'][vmap[v]]['byteStride']=view['byteStride']
    a['bufferView']=vmap[v];amap[index]=len(doc['accessors']);doc['accessors'].append(a);return amap[index]
for action in c['actions']:
    source_clip=next(a for a in original['animations'] if a['name'].split('--')[0]==action['clip'])
    animation=copy.deepcopy(source_clip);animation['name']=action['clip']
    for ch in animation['channels']:
        n=original['nodes'][ch['target']['node']];matches=names.get(n['name'],[]);assert len(matches)==1,n['name']
        dest=doc['nodes'][matches[0]]
        for prop,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:
            assert max(abs(x-y) for x,y in zip(n.get(prop,default),dest.get(prop,default)))<1e-5,(n['name'],prop)
        ch['target']['node']=matches[0]
    for s in animation['samplers']:
        for field in ['input','output']:s[field]=acc(s[field])
    before=next(a for a in doc['animations'] if a['name']==action['clip'])
    doc['animations'][doc['animations'].index(before)]=animation
    report.append({'clip':action['clip'],'oldChannels':len(before['channels']),'officialChannels':len(animation['channels'])})
c['source'].pop('animationReference',None);c['source'].pop('animationReferenceSha256',None)
c['source']['description']='Official JP r96 patch 33 CH0221_NonWeapon; original rig, textures and explicitly bound official scene clips. No community animation substitution.'
save(target/'model.glb',doc,compact(doc,data));(target/'character.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
(R/'test-results/natsu-scene-repair.json').write_text(json.dumps({'source':str(source.relative_to(R)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'clips':report},indent=2),encoding='utf8')
print(report)
