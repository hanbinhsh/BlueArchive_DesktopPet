"""Apply measured vessel clipping to converted furniture (repeatable)."""
import pathlib,sys
from glb import load,save

root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'characters')
path=root/'mine/f207310_0.glb'
doc,binary=load(path);count=0
for material in doc['materials']:
    extra=material.get('extras',{})
    if '/water Pour' in extra.get('BA_cafeParticle',{}).get('sourceName',''):
        extra['BA_liquidReceiver']={'node':'furniture_6_bone_table_01','normal':[0,0,1],'constant':-.052}
        count+=1
if count!=2:raise ValueError(f'Expected two original pour materials, got {count}')
if not any(n.get('name')=='furniture_6_bone_table_01' for n in doc['nodes']):raise ValueError('Missing original cup bone')
save(path,doc,binary)
print('Applied cup receivers:',count)
