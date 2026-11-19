"""Verify common animations and furniture are unchanged while actions expand."""
import hashlib,json,pathlib
from glb import load
R=pathlib.Path(__file__).resolve().parents[1];root=R/'.assets/expanded-ready';old=R/'release/v0.1.18/win-unpacked/resources/characters'
def sha(data):return hashlib.sha256(data).hexdigest()
def accessor(doc,binary,i):
    a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];start=v.get('byteOffset',0)
    return {**{k:x for k,x in a.items() if k!='bufferView'},'data':sha(binary[start:start+v['byteLength']]),'stride':v.get('byteStride')}
def clip(doc,binary,a):
    return {'channels':a['channels'],'samplers':[{**s,'input':accessor(doc,binary,s['input']),'output':accessor(doc,binary,s['output'])} for s in a['samplers']]}
rows=[]
for p in sorted(root.glob('*/character.json')):
    c=json.loads(p.read_text(encoding='utf8'));d,b=load(p.parent/'model.glb');anims={a['name']:a for a in d['animations']}
    assert all(a['clip'] in anims for a in c['actions']),c['id']
    assert all(not x.get('uri') for x in d.get('images',[])+d.get('buffers',[])),c['id']
    assert (p.parent/'thumbnail.png').is_file(),c['id']
    row={'character':c['id'],'actions':len(c['actions']),'modelSha256':sha((p.parent/'model.glb').read_bytes())}
    prior=old/c['id']
    if prior.exists():
        oc=json.loads((prior/'character.json').read_text(encoding='utf8'));od,ob=load(prior/'model.glb');oa={a['name']:a for a in od['animations']}
        assert d['nodes']==od['nodes'],c['id']
        for a in oc['actions']:
            assert any(n['id']==a['id'] and n['clip']==a['clip'] for n in c['actions']),c['id']
            assert clip(od,ob,oa[a['clip']])==clip(d,b,anims[a['clip']]),(c['id'],a['id'])
        for field in ['animations','furniture','scale','yaw','idleBlink']:
            assert c.get(field)==oc.get(field),(c['id'],field)
        for field in ['BA_halo_follow','BA_pet_visibility']:
            before=od['scenes'][0].get('extras',{}).get(field)
            after=d['scenes'][0].get('extras',{}).get(field)
            if field=='BA_pet_visibility' and before:
                assert before['defaults']==after['defaults'],c['id']
                assert all(after['clips'][k]==v for k,v in before['clips'].items()),c['id']
            elif before:assert before==after,c['id']
        for furniture in oc.get('furniture',[]):
            f=prior/furniture['model'];assert f.read_bytes()==(p.parent/f.name).read_bytes(),f.name
        # Compaction may renumber buffers, textures and materials, but never
        # change a previously adapted surface or its embedded texture pixels.
        def material(model,buf,i):
            m=json.loads(json.dumps(model['materials'][i]));info=m.get('pbrMetallicRoughness',{}).get('baseColorTexture')
            if info:
                texture=model['textures'][info['index']];image=model['images'][texture['source']];view=model['bufferViews'][image['bufferView']];start=view.get('byteOffset',0)
                info['index']=sha(buf[start:start+view['byteLength']])
            return m
        assert len(od['meshes'])==len(d['meshes']),c['id']
        for om,nm in zip(od['meshes'],d['meshes']):
            assert len(om['primitives'])==len(nm['primitives']),c['id']
            for op,np in zip(om['primitives'],nm['primitives']):
                assert {k:accessor(od,ob,v) for k,v in op['attributes'].items()}=={k:accessor(d,b,v) for k,v in np['attributes'].items()},c['id']
                if 'indices' in op:assert accessor(od,ob,op['indices'])==accessor(d,b,np['indices']),c['id']
                assert material(od,ob,op['material'])==material(d,b,np['material']),c['id']
        row['unchangedCommonAnimations']=len(oc['actions']);row['unchangedFurniture']=len(oc.get('furniture',[]))
    rows.append(row)
(R/'test-results/expanded-resources.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
print('Verified',len(rows),'packs;',sum(r['actions'] for r in rows),'actions;',sum(r.get('unchangedCommonAnimations',0) for r in rows),'unchanged common actions')
