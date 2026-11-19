"""Correct native mesh pivot Z from original emitters, preserving base geometry."""
import json,shutil
from pathlib import Path
from glb import load,save,read_accessor,append_accessor,compact

sources={}
def walk(n):
    mesh=n.get('mesh');r=n.get('renderer',{})
    if mesh and r.get('m_RenderMode')==4 and r.get('m_Pivot',{}).get('z'):
        values=mesh['positions'];extent=max(v[2] for v in values)-min(v[2] for v in values)
        delta=-2*r['m_Pivot']['z']*extent
        old=sources.setdefault(n['path'],delta)
        assert abs(old-delta)<1e-6,(n['path'],'ambiguous source pivot')
    for c in n['children']:walk(c)
for name in ['cafe-fx-all033','cafe-fx-nested035','cafe-fx036','cafe-phone036']:
    data=json.loads((Path('.assets')/name/'source.json').read_text('utf8'))
    for effect in data['effects'].values():walk(effect)
    del data
stage=Path('.assets/fx036-stage');report=[]
for baseline in Path('characters').glob('*/f*.glb'):
    rel=baseline.relative_to('characters');target=stage/rel
    d,b=load(target if target.exists() else baseline);patched={};changes=[]
    for mesh in d['meshes']:
        for prim in mesh['primitives']:
            material=d['materials'][prim['material']];extra=material.get('extras',{});spec=extra.get('BA_cafeParticle')
            if not spec or extra.get('BA_nativeMeshPivot') or spec['renderer']['m_RenderMode']!=4:continue
            delta=sources.get(spec['sourceName'])
            if not delta:continue
            old=prim['attributes']['POSITION'];key=(old,delta)
            if key not in patched:
                values=[[x,y,z+delta] for x,y,z in read_accessor(d,b,old)]
                index=append_accessor(d,b,values,'VEC3');d['accessors'][index].update(min=[min(v[k] for v in values) for k in range(3)],max=[max(v[k] for v in values) for k in range(3)])
                patched[key]=index
            prim['attributes']['POSITION']=patched[key];extra['BA_nativeMeshPivot']=True
            changes.append({'source':spec['sourceName'],'deltaZ':delta})
    if changes:
        if not target.parent.exists():shutil.copytree(baseline.parent,target.parent)
        save(target,d,compact(d,b));report.append({'path':str(rel),'changes':changes});print(rel,len(changes),flush=True)
Path('test-results/mesh-pivot036-applied.json').write_text(json.dumps(report,indent=2),'utf8')
print('Corrected',len(report),'models; source emitters',len(sources))
