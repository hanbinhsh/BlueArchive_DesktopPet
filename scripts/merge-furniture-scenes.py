"""Share verified identical geometry across furniture clips, without guessing rigs."""
import copy,hashlib,json,re
from pathlib import Path
from glb import load,save,compact,read_accessor
R=Path(__file__).resolve().parents[1];report=[]
def signature(d,b):
    def accessor(i):
        a=d['accessors'][i];return {'type':a['type'],'componentType':a['componentType'],'normalized':a.get('normalized',False),'values':read_accessor(d,b,i)}
    meshes=copy.deepcopy(d['meshes']);skins=copy.deepcopy(d['skins'])
    for m in meshes:
        for p in m['primitives']:
            p['attributes']={k:accessor(v) for k,v in p['attributes'].items()}
            if 'indices'in p:p['indices']=accessor(p['indices'])
    for s in skins:
        if 'inverseBindMatrices'in s:s['inverseBindMatrices']=accessor(s['inverseBindMatrices'])
    images=[]
    for im in d.get('images',[]):
        v=d['bufferViews'][im['bufferView']];start=v.get('byteOffset',0);images.append(hashlib.sha256(b[start:start+v['byteLength']]).hexdigest())
    payload=[d['nodes'],meshes,skins,d.get('materials'),d.get('textures'),d.get('samplers'),images,d['scenes'][0]['nodes']]
    return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
for path in sorted((R/'characters').glob('*/character.json')):
    c=json.loads(path.read_text(encoding='utf8'));groups={}
    for f in c.get('furniture',[]):
        family='bedroom_bed' if f['id'].startswith('bedroom_bed_') else 'bedroom_windowsofa' if f['id'].startswith('bedroom_windowsofa_') else re.sub(r'_\d+$','',f['id'])
        groups.setdefault(family,[]).append(f)
    changed=False
    for family,items in groups.items():
        if len(items)<2:continue
        if all(f.get('sceneId')==family for f in items):continue
        sources=[load(path.parent/f['model']) for f in items]
        hashes=[signature(d,b) for d,b in sources]
        if len(set(hashes))!=1:
            report.append({'character':c['id'],'family':family,'shared':False,'reason':'Geometry or bind transforms differ; preserve separate scenes'});continue
        d=copy.deepcopy(sources[0][0]);data=bytearray(sources[0][1]);d['animations']=[]
        extra=d['scenes'][0]['extras'];extra['BA_pet_visibility']['clips']={}
        mouths={m['material']:m for m in extra.get('BA_furniture_mouths',[])}
        for m in mouths.values():m['events']={}
        for (source,b),item in zip(sources,items):
            while len(data)%4:data.append(0)
            base=len(data);data.extend(b);viewbase=len(d['bufferViews']);accbase=len(d['accessors'])
            views=copy.deepcopy(source['bufferViews'])
            for v in views:v['byteOffset']=v.get('byteOffset',0)+base
            accessors=copy.deepcopy(source['accessors'])
            for a in accessors:
                if 'bufferView'in a:a['bufferView']+=viewbase
                assert 'sparse' not in a
            d['bufferViews'].extend(views);d['accessors'].extend(accessors)
            anim=copy.deepcopy(next(a for a in source['animations'] if a['name']==item['clip']))
            for s in anim['samplers']:s['input']+=accbase;s['output']+=accbase
            d['animations'].append(anim)
            se=source['scenes'][0]['extras'];extra['BA_pet_visibility']['clips'].update(se['BA_pet_visibility']['clips'])
            for m in se.get('BA_furniture_mouths',[]):mouths[m['material']]['events'].update(m['events'])
        extra['BA_furniture']={'sceneId':family,'clips':[f['clip'] for f in items]}
        name='scene_'+family+'.glb';save(path.parent/name,d,compact(d,data))
        for f in items:f['model']=name;f['sceneId']=family
        changed=True;report.append({'character':c['id'],'family':family,'shared':True,'clips':len(items),'geometrySha256':hashes[0]})
    if changed:path.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
(R/'test-results/shared-furniture-scenes.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
